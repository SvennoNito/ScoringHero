import os, pickle
from signal_processing.recompute_derived import recompute_derived
from .write_cache import write_cache
from .ui_to_cache import ui_to_cache, _manipulation_fingerprint


def load_cache(ui):
    cache = {}
    cache_valid = False
    filename = f"{ui.filename}.cache.pkl"
    if os.path.exists(filename):
        with open(filename, "rb") as file:
            cache = pickle.load(file)

        cache_valid = (
            "spectogram" in cache
            and cache.get("Sampling_rate_hz") == ui.config[0]["Sampling_rate_hz"]
            and cache.get("Epoch_length_s") == ui.config[0]["Epoch_length_s"]
            and cache.get("Channel_for_spectogram") == ui.config[0]["Channel_for_spectogram"]
            and cache.get("manipulation_fingerprint") == _manipulation_fingerprint(ui)
        )

    tf_limits_config = ui.config[0].get("Wavelet_frequency_limits_hz", [0.25, 45])
    tf_norm_valid = (
        cache_valid
        and "tf_norm" in cache
        and cache["tf_norm"]["Wavelet_frequency_limits_hz"] == tf_limits_config
    )

    if not cache_valid or not tf_norm_valid:
        # Recompute spectrogram + TF norms from current eeg_data_display
        recompute_derived(ui)
    else:
        ui.power, ui.freqs, ui.freqsOI, ui.swa = cache["spectogram"].values()
        ui.tf_freqs              = cache["tf_norm"]["tf_freqs"]
        ui.tf_norm_median        = cache["tf_norm"]["tf_norm_median"]
        ui.tf_norm_iqr           = cache["tf_norm"]["tf_norm_iqr"]
        ui.tf_norm_rms           = cache["tf_norm"]["tf_norm_rms"]
        ui.tf_norm_median_linear = cache["tf_norm"]["tf_norm_median_linear"]
        # Refresh cache file with current ui state (updates fingerprint etc.)
        write_cache(ui, ui_to_cache(ui))
