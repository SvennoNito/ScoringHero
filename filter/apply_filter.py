import numpy as np
from concurrent.futures import ThreadPoolExecutor
from scipy.signal import cheby2, sosfiltfilt


def apply_filter(eeg_data, sampling_rate, filter_settings):
    """
    Applies Chebyshev Type 2 filters to a copy of eeg_data and returns it.

    All active filters for each channel are merged into a single SOS chain so
    that sosfiltfilt is called at most once per channel (instead of once per
    filter type). Channels are processed in parallel via ThreadPoolExecutor;
    sosfiltfilt releases the GIL, so threads give real parallelism.

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

    # Build one combined SOS array per channel (None if no filter active)
    channel_sos = []
    for settings in filter_settings:
        sections = []

        if settings["hp_enabled"]:
            cutoff = settings["hp_cutoff"]
            order = int(settings["hp_order"])
            if 0 < cutoff < nyquist:
                sections.append(
                    cheby2(order, 60, cutoff, btype="highpass", fs=sampling_rate, output="sos")
                )

        if settings["lp_enabled"]:
            cutoff = settings["lp_cutoff"]
            order = int(settings["lp_order"])
            if 0 < cutoff < nyquist:
                sections.append(
                    cheby2(order, 60, cutoff, btype="lowpass", fs=sampling_rate, output="sos")
                )

        if settings["notch_enabled"]:
            cutoff = settings["notch_cutoff"]
            order = int(settings["notch_order"])
            low, high = cutoff - 1.0, cutoff + 1.0
            if low > 0 and high < nyquist:
                sections.append(
                    cheby2(order, 60, [low, high], btype="bandstop", fs=sampling_rate, output="sos")
                )

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
