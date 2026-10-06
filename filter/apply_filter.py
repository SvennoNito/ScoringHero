import numpy as np
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from scipy.optimize import brentq
from scipy.signal import cheby2, sosfiltfilt, sosfreqz

STOPBAND_DB = 60
# Target zero-phase gain at the cutoff: -3 dB as seen on a sinusoid that goes
# through sosfiltfilt (amplitude ratio 10**(-3/20)).
_TARGET_GAIN = 10.0 ** (-3.0 / 20.0)
NOTCH_HALF_WIDTH_HZ = 1.0  # notch filter is 3 dB down at notch frequency ± this


def zero_phase_gain(sos, freqs, sampling_rate):
    """Amplitude gain of sosfiltfilt (forward-backward = squared magnitude) at freqs (Hz)."""
    _, h = sosfreqz(sos, worN=np.atleast_1d(np.asarray(freqs, dtype=float)), fs=sampling_rate)
    return np.abs(h) ** 2


def _solve(f, lo, hi):
    """Root of monotone f on [lo, hi]; if the target is unreachable, the closest end."""
    f_lo, f_hi = f(lo), f(hi)
    if f_lo * f_hi > 0:
        return lo if abs(f_lo) < abs(f_hi) else hi
    return brentq(f, lo, hi, xtol=1e-12, rtol=1e-12)


@lru_cache(maxsize=256)
def design_filter(kind, cutoff, order, sampling_rate):
    """Chebyshev Type 2 SOS (60 dB stopband) whose zero-phase response is -3 dB
    at `cutoff` Hz ("hp", "lp"), or at cutoff +/- 1 Hz and deepest at `cutoff` ("notch").

    scipy's cheby2 treats the frequency it is given as the -60 dB stopband edge,
    which puts the -3 dB point far from it (and the zero-phase pass squares the
    attenuation again). So the design frequency is searched numerically, once per
    design, until the zero-phase gain at the requested frequency is exactly -3 dB.
    The search runs on the pre-warped (tan) frequency axis, where the bilinear
    transform makes the notch's two -3 dB points symmetric about its centre.

    kind: "hp" | "lp" | "notch". Returns None for an invalid cutoff
    (<= 0 or >= Nyquist; for the notch the +/-1 Hz points must lie inside (0, Nyquist)).
    The returned array is shared (cached): do not modify it.
    """
    fs = sampling_rate
    nyquist = fs / 2.0
    order = int(order)
    warp = lambda f: np.log(np.tan(np.pi * f / fs))        # Hz -> log pre-warped frequency
    unwarp = lambda x: fs / np.pi * np.arctan(np.exp(x))   # and back

    if kind in ("hp", "lp"):
        if not (0 < cutoff < nyquist):
            return None
        btype = "highpass" if kind == "hp" else "lowpass"

        def design(x):
            return cheby2(order, STOPBAND_DB, unwarp(x), btype=btype, fs=fs, output="sos")

        def error(x):
            return zero_phase_gain(design(x), cutoff, fs)[0] - _TARGET_GAIN

        # Stopband edge lies below the cutoff for high-pass, above it for low-pass.
        if kind == "hp":
            x = _solve(error, warp(cutoff * 1e-6), warp(cutoff))
        else:
            x = _solve(error, warp(cutoff), warp(nyquist * (1 - 1e-9)))
        return design(x)

    if kind == "notch":
        low_pt, high_pt = cutoff - NOTCH_HALF_WIDTH_HZ, cutoff + NOTCH_HALF_WIDTH_HZ
        if not (low_pt > 0 and high_pt < nyquist):
            return None
        a, b = np.tan(np.pi * low_pt / fs), np.tan(np.pi * high_pt / fs)
        centre = np.sqrt(a * b)           # geometric centre in warped units
        spread = np.sqrt(b / a) - 1.0     # stopband edges at centre / (1+s*spread) and centre * (1+s*spread)

        def design(x):
            ratio = 1.0 + np.exp(x) * spread
            edges = [fs / np.pi * np.arctan(centre / ratio), fs / np.pi * np.arctan(centre * ratio)]
            return cheby2(order, STOPBAND_DB, edges, btype="bandstop", fs=fs, output="sos")

        def error(x):
            return zero_phase_gain(design(x), low_pt, fs)[0] - _TARGET_GAIN

        # s in (0, 1): stopband edges approach the -3 dB points as s -> 1
        return design(_solve(error, np.log(1e-7), np.log(1 - 1e-9)))

    raise ValueError(f"unknown filter kind: {kind}")


def apply_filter(eeg_data, sampling_rate, filter_settings):
    """
    Applies Chebyshev Type 2 filters to a copy of eeg_data and returns it.
    The cutoff frequency is the -3 dB point of the zero-phase response; see design_filter.

    All active filters for each channel are merged into a single SOS chain so
    that sosfiltfilt is called at most once per channel (instead of once per
    filter type). Channels are processed in parallel via ThreadPoolExecutor;
    sosfiltfilt releases the GIL, so threads give real parallelism.

    Parameters
    ----------
    eeg_data : np.ndarray, shape (n_channels, n_samples)
    sampling_rate : float
    filter_settings : list[dict]
        Channel settings, one per channel (row of eeg_data), read for:
        - Filter_hp_enabled (bool), Filter_hp_cutoff (float), Filter_hp_order (int)
        - Filter_lp_enabled, Filter_lp_cutoff, Filter_lp_order
        - Filter_notch_enabled, Filter_notch_cutoff, Filter_notch_order
        A filter with an invalid cutoff is skipped.

    Returns
    -------
    np.ndarray, shape (n_channels, n_samples)
        New array with filters applied; eeg_data is not modified.
    """
    # Build one combined SOS array per channel (None if no filter active)
    channel_sos = []
    for settings in filter_settings:
        sections = []
        for kind in ("hp", "lp", "notch"):
            if settings[f"Filter_{kind}_enabled"]:
                sos = design_filter(
                    kind, float(settings[f"Filter_{kind}_cutoff"]), int(settings[f"Filter_{kind}_order"]),
                    float(sampling_rate),
                )
                if sos is not None:
                    sections.append(sos)

        channel_sos.append(np.vstack(sections) if sections else None)

    result = eeg_data.copy()

    def _filter_channel(ch_idx):
        sos = channel_sos[ch_idx]
        if sos is None:
            return ch_idx, None
        filtered = sosfiltfilt(sos, eeg_data[ch_idx].astype(np.float64))
        return ch_idx, filtered

    with ThreadPoolExecutor() as executor:
        for ch_idx, filtered in executor.map(_filter_channel, range(len(filter_settings))):
            if filtered is not None:
                result[ch_idx] = filtered

    return result
