import numpy as np
from filter.apply_filter import apply_filter


def rebuild_eeg_data_display(ui):
    """Rebuild ui.eeg_data_display from ui.eeg_data by applying all active manipulations:
    filter → re-reference → polarity flip.
    """
    result = ui.eeg_data.copy()

    # 1. Apply per-channel filter settings (stored in config)
    filter_settings = []
    any_filter_active = False
    for chan in ui.config[1]:
        fs = {
            "hp_enabled":    chan.get("Filter_hp_enabled", False),
            "hp_cutoff":     chan.get("Filter_hp_cutoff", 0.3),
            "hp_order":      chan.get("Filter_hp_order", 4),
            "lp_enabled":    chan.get("Filter_lp_enabled", False),
            "lp_cutoff":     chan.get("Filter_lp_cutoff", 50.0),
            "lp_order":      chan.get("Filter_lp_order", 4),
            "notch_enabled": chan.get("Filter_notch_enabled", False),
            "notch_cutoff":  chan.get("Filter_notch_cutoff", 50.0),
            "notch_order":   chan.get("Filter_notch_order", 4),
        }
        if fs["hp_enabled"] or fs["lp_enabled"] or fs["notch_enabled"]:
            any_filter_active = True
        filter_settings.append(fs)
    if any_filter_active:
        result = apply_filter(result, ui.config[0]["Sampling_rate_hz"], filter_settings)

    # 2. Apply re-referencing
    # Use pre-reref snapshot so every channel's reference is the filtered-only signal,
    # matching the previous display-time behaviour in signalWidget.
    n_data_channels = result.shape[0]
    any_reref = any(ch.get("Re_reference", "None") != "None" for ch in ui.config[1])
    if any_reref:
        pre_reref = result.copy()
        for ch_idx, ch_config in enumerate(ui.config[1]):
            if ch_idx >= n_data_channels:
                break
            reref = ch_config.get("Re_reference", "None")
            if reref != "None":
                ref_idx = next(
                    (i for i, c in enumerate(ui.config[1]) if c["Channel_name"] == reref),
                    None,
                )
                if ref_idx is not None and ref_idx < n_data_channels:
                    result[ch_idx] = pre_reref[ch_idx] - pre_reref[ref_idx]

    # 3. Apply polarity flip
    for ch_idx, ch_config in enumerate(ui.config[1]):
        if ch_idx >= n_data_channels:
            break
        if ch_config.get("Flip_polarity", False):
            result[ch_idx] = -result[ch_idx]

    ui.eeg_data_display = result
