import numpy as np
from scipy.signal import cheby2, sosfiltfilt


def apply_filter(eeg_data, sampling_rate, filter_settings):
    """
    Applies Chebyshev Type 2 filters to a copy of eeg_data and returns it.

    Parameters
    ----------
    eeg_data : np.ndarray, shape (n_channels, n_samples)
    sampling_rate : float
    filter_settings : list[dict]
        One dict per channel with keys:
        - hp_enabled (bool), hp_cutoff (float), hp_order (int)
        - lp_enabled (bool), lp_cutoff (float), lp_order (int)
        - notch_enabled (bool), notch_cutoff (float), notch_order (int)

    Returns
    -------
    np.ndarray, shape (n_channels, n_samples)
        New array with filters applied; eeg_data is not modified.
    """
    nyquist = sampling_rate / 2.0
    result = eeg_data.copy()

    for ch_idx, settings in enumerate(filter_settings):
        data = eeg_data[ch_idx].astype(np.float64)
        changed = False

        # High-pass
        if settings["hp_enabled"]:
            cutoff = settings["hp_cutoff"]
            order = int(settings["hp_order"])
            if 0 < cutoff < nyquist:
                sos = cheby2(order, 40, cutoff, btype="highpass", fs=sampling_rate, output="sos")
                data = sosfiltfilt(sos, data)
                changed = True

        # Low-pass
        if settings["lp_enabled"]:
            cutoff = settings["lp_cutoff"]
            order = int(settings["lp_order"])
            if 0 < cutoff < nyquist:
                sos = cheby2(order, 40, cutoff, btype="lowpass", fs=sampling_rate, output="sos")
                data = sosfiltfilt(sos, data)
                changed = True

        # Notch (bandstop ±1 Hz around the cutoff frequency)
        if settings["notch_enabled"]:
            cutoff = settings["notch_cutoff"]
            order = int(settings["notch_order"])
            low, high = cutoff - 1.0, cutoff + 1.0
            if low > 0 and high < nyquist:
                sos = cheby2(order, 40, [low, high], btype="bandstop", fs=sampling_rate, output="sos")
                data = sosfiltfilt(sos, data)
                changed = True

        if changed:
            result[ch_idx] = data

    return result
