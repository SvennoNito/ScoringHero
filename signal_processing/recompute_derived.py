import numpy as np
from .spectogram_to_ui import spectogram_to_ui
from cache.ui_to_cache import ui_to_cache
from cache.write_cache import write_cache


def recompute_derived(ui):
    """Recompute spectrogram, SWA, and TF norms from the current ui.eeg_data_display,
    then update the cache on disk.

    Call this whenever eeg_data_display changes (filter applied, re-ref changed, etc.)
    or whenever spectrogram parameters change (channel, sampling rate, epoch length).
    """
    ui.power, ui.freqs, ui.freqsOI, ui.swa = spectogram_to_ui(ui)

    # Recompute TF normalisation statistics from the new spectrogram
    tf_limits = ui.config[0].get("Wavelet_frequency_limits_hz", [0.25, 45])
    srate     = ui.config[0]["Sampling_rate_hz"]
    min_freq  = max(float(tf_limits[0]), 0.1)
    max_freq  = min(float(tf_limits[1]), srate / 2 - 0.25)
    tf_freqs  = np.geomspace(min_freq, max_freq, 120)
    ui.tf_freqs = tf_freqs

    log_power    = np.log10(np.maximum(ui.power, 1e-30))
    median_welch = np.median(log_power, axis=0)
    iqr_welch    = (np.percentile(log_power, 75, axis=0)
                    - np.percentile(log_power, 25, axis=0))
    iqr_welch    = np.maximum(iqr_welch, 1e-6)
    rms_welch    = np.sqrt(np.mean(log_power ** 2, axis=0))
    rms_welch    = np.maximum(rms_welch, 1e-6)

    ui.tf_norm_median = np.interp(tf_freqs, ui.freqs, median_welch)
    ui.tf_norm_iqr    = np.interp(tf_freqs, ui.freqs, iqr_welch)
    ui.tf_norm_rms    = np.interp(tf_freqs, ui.freqs, rms_welch)

    median_linear_welch     = np.median(ui.power, axis=0)
    median_linear_welch     = np.maximum(median_linear_welch, 1e-30)
    ui.tf_norm_median_linear = np.interp(tf_freqs, ui.freqs, median_linear_welch)

    write_cache(ui, ui_to_cache(ui))
