import numpy as np
from filter.apply_filter import apply_filter


def _apply_manipulations(source, config):
    """Apply re-reference -> filter -> polarity flip to a raw (channels x samples)
    array, using the per-channel settings stored in config[1].

    Re-referencing comes first so that each channel's filter settings act on
    exactly the signal that is displayed.  Filtering is linear, so for a channel
    A referenced to B this only matters when A and B carry different filter
    settings -- but they are configured independently (and a derived channel
    added in the config window starts out with no filter at all), so forming
    A - B from the *raw* signals is the only order that makes the Ctrl+F
    settings of a re-referenced channel behave as the user expects.  Filtering
    first would leave the reference channel's unfiltered content in the
    difference.
    """
    result = source.copy()
    n_data_channels = result.shape[0]

    # 1. Apply re-referencing
    # Reference against the raw (unfiltered, un-rereferenced, unflipped) signal so
    # that the reference channel's own settings never leak into this channel.
    any_reref = any(ch.get("Re_reference", "None") != "None" for ch in config[1])
    if any_reref:
        for ch_idx, ch_config in enumerate(config[1]):
            if ch_idx >= n_data_channels:
                break
            reref = ch_config.get("Re_reference", "None")
            if reref != "None":
                ref_idx = next(
                    (i for i, c in enumerate(config[1]) if c["Channel_name"] == reref),
                    None,
                )
                if ref_idx is not None and ref_idx < n_data_channels:
                    result[ch_idx] = source[ch_idx] - source[ref_idx]

    # 2. Apply per-channel filter settings (stored in config)
    filter_settings = []
    any_filter_active = False
    for chan in config[1][:n_data_channels]:
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
        result = apply_filter(result, config[0]["Sampling_rate_hz"], filter_settings)

    # 3. Apply polarity flip
    for ch_idx, ch_config in enumerate(config[1]):
        if ch_idx >= n_data_channels:
            break
        if ch_config.get("Flip_polarity", False):
            result[ch_idx] = -result[ch_idx]

    return result


def rebuild_eeg_data_display(ui):
    """Rebuild ui.eeg_data_display from ui.eeg_data by applying all active manipulations:
    re-reference -> filter -> polarity flip.

    If an overlay signal is loaded (ui.eeg_data_ref), the same manipulations are
    applied to it too, producing ui.eeg_data_display_ref, so that filtering,
    re-referencing, and polarity flips always stay in sync between the two signal sets.
    """
    ui.eeg_data_display = _apply_manipulations(ui.eeg_data, ui.config)

    if getattr(ui, "eeg_data_ref", None) is not None:
        ui.eeg_data_display_ref = _apply_manipulations(ui.eeg_data_ref, ui.config)
    else:
        ui.eeg_data_display_ref = None
