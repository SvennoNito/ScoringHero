"""
MT-Spindle: Multitaper-based Sleep Spindle Detection.

Directly adapts the MT-KCD approach (Oliveira et al. 2020) for sigma-band
spindle detection. Candidate regions are identified from median-normalized
sigma-band spectrogram power using the same percentile approach as MT-KCD.
Spindle boundaries are refined using the Hilbert envelope of the sigma-band
filtered signal.
"""

import numpy as np
from scipy.signal import butter, filtfilt, hilbert
from scipy.signal.windows import dpss
from scipy.ndimage import uniform_filter1d


def _bandpass(x, sfreq, low=0.3, high=35.0):
    nyq = sfreq / 2.0
    b, a = butter(4, [low / nyq, min(high / nyq, 0.999)], btype="band")
    return filtfilt(b, a, x)


def _cma(x, window):
    """Central moving average via uniform_filter1d (O(N))."""
    w = max(1, int(window))
    return uniform_filter1d(x.astype(float), size=w, mode="nearest")


def _next_pow2(n):
    p = 1
    while p < n:
        p <<= 1
    return p


def _compute_spectrogram(x, sfreq, L, delta_j, delta_f):
    """Multitaper spectrogram. Returns SG in dB (10*log10(power+1)), J, R."""
    N = len(x)
    TW = (L * delta_f) / (2.0 * sfreq)
    K = max(1, int(2 * TW) - 1)

    tapers = dpss(L, TW, Kmax=K)
    if tapers.ndim == 1:
        tapers = tapers[np.newaxis, :]

    R = _next_pow2(L)
    J = int(np.ceil(N / delta_j))
    half = R // 2 + 1

    SG = np.zeros((half, J), dtype=np.float64)
    for j in range(J):
        start = j * delta_j
        seg = np.zeros(L)
        avail = min(L, N - start)
        if avail > 0:
            seg[:avail] = x[start: start + avail]
        SW = np.zeros(half)
        for k in range(K):
            tapered = tapers[k] * seg
            fft_out = np.fft.rfft(tapered, n=R)
            SW += (1.0 / sfreq) * np.abs(fft_out) ** 2 / K
        SG[:, j] = SW

    SG = 10.0 * np.log10(SG + 1.0)
    return SG, J, R


def _identify_candidate_regions(SG, J, R, sfreq, fmin, fmax, Ishort, Ibackg, q):
    """
    Find candidate spindle regions from median-normalized sigma-band power.

    Subtracts per-frequency median from the spectrogram (dB above median
    baseline) before summing sigma-band power, making the threshold
    independent of absolute signal amplitude. Uses the same percentile
    approach as MT-KCD.

    Returns list of (j1, j2) inclusive spectrogram-column pairs.
    """
    freqs = np.arange(SG.shape[0]) * (sfreq / R)
    mask = (freqs >= fmin) & (freqs <= fmax)
    if not np.any(mask):
        return []

    # dB above per-frequency median baseline
    SG_norm = SG[mask, :] - np.median(SG[mask, :], axis=1, keepdims=True)

    # Sum normalized sigma-band power per spectrogram column
    C = SG_norm.sum(axis=0)

    # Short vs background moving average (same as MT-KCD)
    Cshort = _cma(C, Ishort)
    Cbackg = _cma(C, Ibackg)
    Cdiff = Cshort - Cbackg

    # Percentile threshold (same as MT-KCD)
    thresh = np.percentile(Cdiff, q)
    above = Cdiff >= thresh

    regions = []
    in_region = False
    j1 = 0
    for j in range(J):
        if above[j] and not in_region:
            j1 = j
            in_region = True
        elif not above[j] and in_region:
            regions.append((j1, j - 1))
            in_region = False
    if in_region:
        regions.append((j1, J - 1))

    return regions


def detect_spindle(
    signal,
    sfreq,
    fmin=11.0,
    fmax=16.0,
    amin=10.0,
    dmin_s=0.5,
    dmax_s=2.0,
    q=95.0,
):
    """
    Detect sleep spindles in a single-channel EEG signal.

    Parameters
    ----------
    signal : array-like, shape (N,)
        EEG signal in µV.
    sfreq : float
        Sampling frequency in Hz.
    fmin : float
        Lower bound of sigma band (Hz). Default: 11.0.
    fmax : float
        Upper bound of sigma band (Hz). Default: 16.0.
    amin : float
        Minimum peak envelope amplitude of sigma-band signal (µV). Default: 10.0.
    dmin_s : float
        Minimum spindle duration (s). Default: 0.5.
    dmax_s : float
        Maximum spindle duration (s). Default: 2.0.
    q : float
        Percentile rank for candidate-region threshold (0–100). Default: 95.0.

    Returns
    -------
    events : list of [float, float]
        Detected spindles as [[start_sec, end_sec], ...].
    """
    x = np.asarray(signal, dtype=np.float64)
    N = len(x)

    # Scale sample-based parameters to actual sfreq (same as MT-KCD)
    L       = max(2, int(round(sfreq)))
    delta_j = max(1, int(round(0.05 * sfreq)))
    delta_f = 4.0
    Ishort  = max(1, int(round(0.5 * sfreq / delta_j)))
    Ibackg  = 10 * Ishort
    Lsmth   = max(1, int(round(0.15 * sfreq)))
    Lbackg  = delta_j * Ibackg
    Dmin    = int(round(dmin_s * sfreq))
    Dmax    = int(round(dmax_s * sfreq))

    # 1. Broadband bandpass (same as MT-KCD)
    x_broad = _bandpass(x, sfreq)

    # 2. Multitaper spectrogram
    SG, J, R = _compute_spectrogram(x_broad, sfreq, L, delta_j, delta_f)

    # 3. Candidate regions from median-normalized sigma-band power
    regions = _identify_candidate_regions(SG, J, R, sfreq, fmin, fmax, Ishort, Ibackg, q)
    if not regions:
        return []

    # 4. Sigma-band envelope for boundary detection
    x_sigma = _bandpass(x, sfreq, low=fmin, high=fmax)
    envelope = np.abs(hilbert(x_sigma))
    env_smooth = _cma(envelope, Lsmth)
    env_backg = _cma(env_smooth, Lbackg)

    # 5. Find spindle boundaries within candidate regions
    spindles = []
    for j1, j2 in regions:
        n_start = max(0, j1 * delta_j)
        n_end   = min(N, j2 * delta_j + Dmax)

        above_bg = env_smooth[n_start:n_end] > env_backg[n_start:n_end]

        diff = np.diff(above_bg.astype(np.int8), prepend=0, append=0)
        starts_local = np.where(diff == 1)[0]
        ends_local   = np.where(diff == -1)[0]

        for s, e in zip(starts_local, ends_local):
            n1, n2 = n_start + s, n_start + e
            dur  = n2 - n1
            peak = np.max(env_smooth[n1:n2]) if n2 > n1 else 0.0
            if Dmin <= dur < Dmax and peak >= amin:
                spindles.append((n1, n2))

    events = [[n1 / sfreq, n2 / sfreq] for n1, n2 in spindles]
    return events
