def _manipulation_fingerprint(ui):
    """Tuple capturing all per-channel settings that affect eeg_data_display."""
    return tuple(
        (
            ch.get("Filter_hp_enabled", False), ch.get("Filter_hp_cutoff", 0.3), ch.get("Filter_hp_order", 4),
            ch.get("Filter_lp_enabled", False), ch.get("Filter_lp_cutoff", 50.0), ch.get("Filter_lp_order", 4),
            ch.get("Filter_notch_enabled", False), ch.get("Filter_notch_cutoff", 50.0), ch.get("Filter_notch_order", 4),
            ch.get("Re_reference", "None"),
            ch.get("Flip_polarity", False),
        )
        for ch in ui.config[1]
    )


def ui_to_cache(ui, cache=None):
    if cache is None:
        cache = {}
    cache["spectogram"] = {}
    cache["spectogram"]["power"] = ui.power
    cache["spectogram"]["freqs"] = ui.freqs
    cache["spectogram"]["freqsOI"] = ui.freqsOI
    cache["spectogram"]["swa"] = ui.swa

    cache["Sampling_rate_hz"] = ui.config[0]["Sampling_rate_hz"]
    cache["Epoch_length_s"] = ui.config[0]["Epoch_length_s"]
    cache["Channel_for_spectogram"] = ui.config[0]["Channel_for_spectogram"]
    cache["manipulation_fingerprint"] = _manipulation_fingerprint(ui)

    if hasattr(ui, "tf_freqs"):
        cache["tf_norm"] = {
            "tf_freqs": ui.tf_freqs,
            "tf_norm_median": ui.tf_norm_median,
            "tf_norm_iqr": ui.tf_norm_iqr,
            "tf_norm_rms": ui.tf_norm_rms,
            "tf_norm_median_linear": ui.tf_norm_median_linear,
            "Wavelet_frequency_limits_hz": ui.config[0].get("Wavelet_frequency_limits_hz", [0.25, 45]),
        }
    return cache
