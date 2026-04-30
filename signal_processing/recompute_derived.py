import numpy as np
from .spectogram_to_ui import spectogram_to_ui
from .compute_epoch_periodogram import precompute_all_epoch_periodograms
from cache.ui_to_cache import ui_to_cache
from cache.write_cache import write_cache


def recompute_derived(ui):
    """Recompute spectrogram, SWA, TF norms, and epoch periodograms from the current ui.eeg_data_display,
    then update the cache on disk.

    Call this whenever eeg_data_display changes (filter applied, re-ref changed, etc.)
    or whenever spectrogram/periodogram parameters change (channel, sampling rate, epoch length).
    """
    ui.power, ui.freqs, ui.freqsOI, ui.swa = spectogram_to_ui(ui)

    # Precompute Welch periodograms for all epochs
    precompute_all_epoch_periodograms(ui)

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

    # Precompute normalization stats on linear-frequency grid (for fast colorbar updates)
    freqs_linear = np.linspace(tf_freqs[0], tf_freqs[-1], len(tf_freqs))
    ui.tf_norm_median_linear_grid = np.interp(freqs_linear, tf_freqs, ui.tf_norm_median)
    ui.tf_norm_iqr_linear_grid = np.interp(freqs_linear, tf_freqs, ui.tf_norm_iqr)
    ui.tf_norm_rms_linear_grid = np.interp(freqs_linear, tf_freqs, ui.tf_norm_rms)

    # Precompute L2 normalization scale factors (per-frequency constant for normalization)
    n_cycles_arr = np.maximum(3.0, tf_freqs / 2.0)
    epoch_len = ui.config[0]["Epoch_length_s"]
    ext_lens = ui.config[0].get("Extension_epoch_s", [1, 1])
    if isinstance(ext_lens, (int, float)):
        ext_total = 2 * ext_lens
    else:
        ext_total = sum(ext_lens)
    signal_len = int((epoch_len + ext_total) * srate)
    fft_freqs = np.fft.fftfreq(signal_len, d=1.0 / srate)
    tf_l2_scale_sq = np.zeros(len(tf_freqs), dtype=np.float32)
    for i, freq in enumerate(tf_freqs):
        sigma_f = freq / n_cycles_arr[i]
        wavelet_fft = np.exp(-0.5 * ((fft_freqs - freq) / sigma_f) ** 2)
        tf_l2_scale_sq[i] = np.sum(wavelet_fft ** 2)
    ui.tf_l2_scale_sq = tf_l2_scale_sq

    # Initialize in-memory cache for raw Morlet power by epoch (cleared on channel/freq changes)
    ui.tf_cache = {}

    write_cache(ui, ui_to_cache(ui))
