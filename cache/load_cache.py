import os, pickle
import numpy as np
from signal_processing.spectogram_to_ui import spectogram_to_ui
from .write_cache import write_cache
from .ui_to_cache import ui_to_cache


def load_cache(ui):
    cache = {}
    is_same_spectogram_parameters = False
    filename = f"{ui.filename}.cache.pkl"
    if os.path.exists(filename):
        with open(filename, "rb") as file:
            cache = pickle.load(file)

        # Did spectogram parameters change?
        is_same_spectogram_parameters = (
            cache["Sampling_rate_hz"] == ui.config[0]["Sampling_rate_hz"]
            and cache["Epoch_length_s"] == ui.config[0]["Epoch_length_s"]
            and cache["Channel_for_spectogram"] == ui.config[0]["Channel_for_spectogram"]
            and "spectogram" in cache
        )

    # Spectogram
    if not is_same_spectogram_parameters:
        ui.power, ui.freqs, ui.freqsOI, ui.swa = spectogram_to_ui(ui)
        cache = ui_to_cache(ui, cache)
    else:
        ui.power, ui.freqs, ui.freqsOI, ui.swa = cache["spectogram"].values()

    # TF normalization — restore from cache if frequency limits unchanged, else recompute.
    tf_limits_config = ui.config[0].get("Wavelet_frequency_limits_hz", [0.25, 45])
    if (
        "tf_norm" in cache
        and cache["tf_norm"]["Wavelet_frequency_limits_hz"] == tf_limits_config
    ):
        ui.tf_freqs              = cache["tf_norm"]["tf_freqs"]
        ui.tf_norm_median        = cache["tf_norm"]["tf_norm_median"]
        ui.tf_norm_iqr           = cache["tf_norm"]["tf_norm_iqr"]
        ui.tf_norm_rms           = cache["tf_norm"]["tf_norm_rms"]
        ui.tf_norm_median_linear = cache["tf_norm"]["tf_norm_median_linear"]
    else:
        # ui.power : (n_epochs, n_freqs_welch), linear scale
        # ui.freqs : (n_freqs_welch,), 0 to Nyquist in 1/winlen Hz steps
        srate    = ui.config[0]["Sampling_rate_hz"]
        min_freq = max(float(tf_limits_config[0]), 0.1)
        max_freq = min(float(tf_limits_config[1]), srate / 2 - 0.25)
        tf_freqs = np.geomspace(min_freq, max_freq, 120)
        ui.tf_freqs = tf_freqs

        log_power   = np.log10(np.maximum(ui.power, 1e-30))
        median_welch = np.median(log_power, axis=0)
        iqr_welch    = (np.percentile(log_power, 75, axis=0)
                        - np.percentile(log_power, 25, axis=0))
        iqr_welch    = np.maximum(iqr_welch, 1e-6)
        rms_welch    = np.sqrt(np.mean(log_power ** 2, axis=0))
        rms_welch    = np.maximum(rms_welch, 1e-6)

        ui.tf_norm_median = np.interp(tf_freqs, ui.freqs, median_welch)
        ui.tf_norm_iqr    = np.interp(tf_freqs, ui.freqs, iqr_welch)
        ui.tf_norm_rms    = np.interp(tf_freqs, ui.freqs, rms_welch)

        median_linear_welch = np.median(ui.power, axis=0)
        median_linear_welch = np.maximum(median_linear_welch, 1e-30)
        ui.tf_norm_median_linear = np.interp(tf_freqs, ui.freqs, median_linear_welch)

    # Write cache (ui_to_cache updates tf_norm now that tf_freqs is set)
    cache = ui_to_cache(ui, cache)
    write_cache(ui, cache)
