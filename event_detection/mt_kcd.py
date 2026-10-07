"""
MT-KCD: Multitaper-based K-Complex Detection.

Implementation of the method described in:
  Oliveira et al. (2020), Expert Systems With Applications 151, 113331.
  "Multitaper-based method for automatic k-complex detection in human sleep EEG"

All default parameter values are taken from Table 1 of that paper (Fs = 200 Hz).
Parameters that depend on sampling rate are scaled automatically.
"""

import numpy as np
from scipy.signal import butter, filtfilt
from scipy.signal.windows import dpss
from scipy.ndimage import uniform_filter1d


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Algorithm 1 – Multitaper spectrogram
# ---------------------------------------------------------------------------

def _compute_spectrogram(x, sfreq, L, delta_j, delta_f):
    """
    Returns SG (shape: [R//2+1, J]), J, R.
    SG values are in dB (10*log10(power + 1)).
    """
    N = len(x)
    TW = (L * delta_f) / (2.0 * sfreq)
    K = max(1, int(2 * TW) - 1)

    tapers = dpss(L, TW, Kmax=K)           # shape (K, L) or (L,) when K==1
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


# ---------------------------------------------------------------------------
# Algorithm 2 – Candidate regions identification
# ---------------------------------------------------------------------------

def _identify_candidate_regions(SG, J, R, sfreq, fmax, Ishort, Ibackg, q):
    """Returns list of (j1, j2) inclusive spectrogram-column pairs."""
    # Frequency axis (one-sided)
    freqs = np.arange(SG.shape[0]) * (sfreq / R)

    # Eq. 10: sum delta-band power per column
    mask = freqs <= fmax
    C = SG[mask, :].sum(axis=0)            # shape (J,)

    # Eq. 11: short and background moving averages
    Cshort = _cma(C, Ishort)
    Cbackg = _cma(C, Ibackg)

    # Eq. 12: difference
    Cdiff = Cshort - Cbackg

    # Threshold at q-th percentile
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


# ---------------------------------------------------------------------------
# Algorithm 3 – Candidate KCs marking
# ---------------------------------------------------------------------------

def _mark_kc_candidates(x, N, regions, delta_j, Lsmth, Lbackg):
    """Returns list of (n1, n2) sample-index pairs for candidate KCs."""
    x_smth  = _cma(x, Lsmth)
    x_backg = _cma(x, Lbackg)
    sigma   = _cmsd(x, Lbackg)

    A_inf = x_backg - sigma
    A_sup = x_backg + sigma

    # Transition points: n where x_smth[n] >= x_backg[n] but x_smth[n+1] < x_backg[n+1]
    above = x_smth >= x_backg
    transitions = np.where(above[:-1] & ~above[1:])[0]  # vectorised

    # Waveforms between consecutive transition points
    KCcand = []
    for i in range(len(transitions) - 1):
        n1, n2 = int(transitions[i]), int(transitions[i + 1])

        # Check if n1 falls inside any candidate region
        in_region = any(j1 * delta_j <= n1 <= j2 * delta_j for j1, j2 in regions)
        if not in_region:
            continue

        # Amplitude condition: x_smth must dip below A_inf AND rise above A_sup
        seg_smth = x_smth[n1: n2 + 1]
        seg_inf  = A_inf[n1: n2 + 1]
        seg_sup  = A_sup[n1: n2 + 1]
        if np.any(seg_smth <= seg_inf) and np.any(seg_smth >= seg_sup):
            KCcand.append((n1, n2))

    return KCcand


# ---------------------------------------------------------------------------
# Algorithm 4 – Candidates elimination
# ---------------------------------------------------------------------------

def _eliminate_candidates(x, regions, KCcand, delta_j, Amin, Dmax):
    """Returns list of (n1, n2) accepted KC sample-index pairs."""
    # One candidate per region: keep the one with max peak-to-peak amplitude
    KCmax = []
    for j1, j2 in regions:
        pool = [(n1, n2) for n1, n2 in KCcand if j1 * delta_j <= n1 <= j2 * delta_j]
        if not pool:
            continue
        best = max(pool, key=lambda p: np.ptp(x[p[0]: p[1] + 1]))
        KCmax.append(best)

    # Amplitude >= Amin AND duration < Dmax
    KCout = [
        (n1, n2) for n1, n2 in KCmax
        if np.ptp(x[n1: n2 + 1]) >= Amin and (n2 - n1) < Dmax
    ]
    return KCout


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def detect_kc(
    signal,
    sfreq,
    amin=75.0,
    dmax_s=2.0,
    q=95.0,
    fmax=3.0,
):
    """
    Detect K-complexes in a single-channel EEG signal.

    Parameters
    ----------
    signal : array-like, shape (N,)
        EEG signal in µV.
    sfreq : float
        Sampling frequency in Hz.
    amin : float
        Minimum peak-to-peak amplitude (µV). Default: 75.
    dmax_s : float
        Maximum KC duration (s). Default: 2.0.
    q : float
        Percentile rank for candidate-region threshold (0–100). Default: 95.
    fmax : float
        Upper frequency bound for KC power concentration (Hz). Default: 3.0.

    Returns
    -------
    events : list of [float, float]
        Detected KCs as [[start_sec, end_sec], ...].
    """
    x = np.asarray(signal, dtype=np.float64)
    N = len(x)

    # --- scale all sample-based parameters to actual sfreq ---
    L       = max(2, int(round(sfreq)))            # 1 s window
    delta_j = max(1, int(round(0.05 * sfreq)))     # 0.05 s step
    delta_f = 4.0                                  # Hz, spectral resolution (fixed)
    Ishort  = max(1, int(round(0.5 * sfreq / delta_j)))   # ≈ 0.5 s of spectrogram cols
    Ibackg  = 10 * Ishort                                  # ≈ 5 s
    Lsmth   = max(1, int(round(0.15 * sfreq)))     # 0.15 s smoothing
    Lbackg  = delta_j * Ibackg                     # 5 s amplitude background
    Dmax    = int(round(dmax_s * sfreq))           # max duration in samples

    # 1. Bandpass filter
    x = _bandpass(x, sfreq)

    # 2. Multitaper spectrogram
    SG, J, R = _compute_spectrogram(x, sfreq, L, delta_j, delta_f)

    # 3. Candidate regions
    regions = _identify_candidate_regions(SG, J, R, sfreq, fmax, Ishort, Ibackg, q)
    if not regions:
        return []

    # 4. Candidate KC marking
    KCcand = _mark_kc_candidates(x, N, regions, delta_j, Lsmth, Lbackg)
    if not KCcand:
        return []

    # 5 + 6. Elimination
    KCout = _eliminate_candidates(x, regions, KCcand, delta_j, amin, Dmax)

    # Convert sample indices to seconds
    events = [[n1 / sfreq, n2 / sfreq] for n1, n2 in KCout]
    return events
