"""
MT-Spindle: Multitaper-based Spindle Detection with dB Normalization.

Adapted from MT-KCD (Oliveira et al. 2020) for detection of sleep spindles.
Spindles are detected as power bursts in the 11-16 Hz frequency band,
with dB normalization against a median baseline to enhance detection.

Parameters:
- fmin, fmax: frequency band for spindle detection (default: 11-16 Hz)
- amin_db: minimum power elevation in dB above median baseline (default: 3.0 dB)
- dmin, dmax: minimum and maximum spindle duration (s)
- q: percentile rank for candidate-region threshold
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


def _cmsd(x, window):
    """Central moving standard deviation."""
    mean = _cma(x, window)
    mean_sq = _cma(x ** 2, window)
    return np.sqrt(np.maximum(0.0, mean_sq - mean ** 2))


def _next_pow2(n):
    p = 1
    while p < n:
        p <<= 1
    return p


def _compute_spectrogram(x, sfreq, L, delta_j, delta_f):
    """
    Returns SG (shape: [R//2+1, J]), J, R.
    SG values are in dB (10*log10(power + 1)).
    """
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


def _identify_candidate_regions_db(SG, J, R, sfreq, fmin, fmax, Ishort, Ibackg):
    """
    Identify candidate regions using dB-normalized power.
    Returns list of (j1, j2) inclusive spectrogram-column pairs.
    """
    freqs = np.arange(SG.shape[0]) * (sfreq / R)

    # Sum spindle-band power per column (already in dB)
    mask = (freqs >= fmin) & (freqs <= fmax)
    C = SG[mask, :].sum(axis=0)

    # Short moving average relative to background
    Cshort = _cma(C, Ishort)
    Cbackg = _cma(C, Ibackg)

    # dB difference from background
    Cdiff = Cshort - Cbackg

    # Dynamic threshold based on median absolute deviation
    median_diff = np.median(Cdiff)
    mad = np.median(np.abs(Cdiff - median_diff))
    if mad < 0.1:
        mad = 0.1
    thresh = median_diff + 2.5 * mad

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


def _mark_spindle_candidates(x, N, regions, delta_j, Lsmth, Lbackg):
    """Returns list of (n1, n2) sample-index pairs for candidate spindles."""
    x_smth  = _cma(x, Lsmth)
    x_backg = _cma(x, Lbackg)
    sigma   = _cmsd(x, Lbackg)

    A_inf = x_backg - 0.5 * sigma
    A_sup = x_backg + 0.5 * sigma

    # Transition points
    above = x_smth >= x_backg
    transitions = np.where(above[:-1] & ~above[1:])[0]

    candidates = []
    for i in range(len(transitions) - 1):
        n1, n2 = int(transitions[i]), int(transitions[i + 1])

        # Check if n1 falls inside any candidate region
        in_region = any(j1 * delta_j <= n1 <= j2 * delta_j for j1, j2 in regions)
        if not in_region:
            continue

        # Amplitude condition
        seg_smth = x_smth[n1: n2 + 1]
        seg_inf  = A_inf[n1: n2 + 1]
        seg_sup  = A_sup[n1: n2 + 1]
        if np.any(seg_smth <= seg_inf) and np.any(seg_smth >= seg_sup):
            candidates.append((n1, n2))

    return candidates


def _eliminate_candidates(x, regions, candidates, delta_j, amin_db, dmin, dmax):
    """Returns list of (n1, n2) accepted spindle sample-index pairs."""
    # One candidate per region: keep the one with max power
    best_per_region = []
    for j1, j2 in regions:
        pool = [(n1, n2) for n1, n2 in candidates if j1 * delta_j <= n1 <= j2 * delta_j]
        if not pool:
            continue
        best = max(pool, key=lambda p: np.max(x[p[0]: p[1] + 1]))
        best_per_region.append(best)

    # Filter by amplitude (in dB) and duration constraints
    spindles_out = []
    median_baseline = np.median(x)
    for n1, n2 in best_per_region:
        seg = x[n1: n2 + 1]
        max_power = np.max(seg)
        power_db = max_power - median_baseline
        duration_samples = (n2 - n1)
        if power_db >= amin_db and dmin <= duration_samples < dmax:
            spindles_out.append((n1, n2))

    return spindles_out


def detect_spindle(
    signal,
    sfreq,
    fmin=11.0,
    fmax=16.0,
    amin_db=3.0,
    dmin_s=0.5,
    dmax_s=2.0,
    q=85.0,
):
    """
    Detect sleep spindles in a single-channel EEG signal using dB normalization.

    Parameters
    ----------
    signal : array-like, shape (N,)
        EEG signal in µV.
    sfreq : float
        Sampling frequency in Hz.
    fmin : float
        Minimum spindle frequency (Hz). Default: 11.0.
    fmax : float
        Maximum spindle frequency (Hz). Default: 16.0.
    amin_db : float
        Minimum power elevation in dB above median baseline. Default: 3.0.
    dmin_s : float
        Minimum spindle duration (s). Default: 0.5.
    dmax_s : float
        Maximum spindle duration (s). Default: 2.0.
    q : float
        Percentile rank for candidate-region threshold (0–100). Default: 85.0.

    Returns
    -------
    events : list of [float, float]
        Detected spindles as [[start_sec, end_sec], ...].
    """
    x = np.asarray(signal, dtype=np.float64)
    N = len(x)

    # Scale sample-based parameters to actual sfreq
    L       = max(2, int(round(sfreq)))
    delta_j = max(1, int(round(0.05 * sfreq)))
    delta_f = 4.0
    Ishort  = max(1, int(round(0.5 * sfreq / delta_j)))
    Ibackg  = 10 * Ishort
    Lsmth   = max(1, int(round(0.15 * sfreq)))
    Lbackg  = delta_j * Ibackg
    Dmin    = int(round(dmin_s * sfreq))
    Dmax    = int(round(dmax_s * sfreq))

    # 1. Bandpass filter to spindle band
    x_filt = _bandpass(x, sfreq, low=fmin - 1.0, high=fmax + 1.0)

    # 2. Compute envelope via Hilbert transform
    analytic = hilbert(x_filt)
    envelope = np.abs(analytic)

    # 3. Multitaper spectrogram
    SG, J, R = _compute_spectrogram(x_filt, sfreq, L, delta_j, delta_f)

    # 4. Candidate regions using dB-normalized power
    regions = _identify_candidate_regions_db(SG, J, R, sfreq, fmin, fmax, Ishort, Ibackg)
    if not regions:
        return []

    # 5. Candidate spindle marking
    envelope_smooth = _cma(envelope, Lsmth)
    candidates = _mark_spindle_candidates(envelope_smooth, N, regions, delta_j, Lsmth, Lbackg)
    if not candidates:
        return []

    # 6. Elimination using dB normalization
    envelope_db = 10.0 * np.log10(np.maximum(envelope_smooth, 1.0))
    spindles = _eliminate_candidates(envelope_db, regions, candidates, delta_j, amin_db, Dmin, Dmax)

    # Convert sample indices to seconds
    events = [[n1 / sfreq, n2 / sfreq] for n1, n2 in spindles]
    return events
