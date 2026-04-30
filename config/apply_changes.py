import numpy as np
from .write_configuration import write_configuration
from eeg.number_of_epochs import number_of_epochs
from scoring.default_scoring import default_scoring
from signal_processing.compute_epoch_periodogram import (
    compute_epoch_periodogram,
    precompute_all_epoch_periodograms,
)
from signal_processing.times_vector import times_vector
from signal_processing.freqs_of_interest import freqs_of_interest
from signal_processing.recompute_derived import recompute_derived
from utilities.redraw_gui import redraw_gui
from utilities.apply_tf_visibility import apply_tf_visibility
from utilities.channel_index import rebuild_channel_index
from eeg.rebuild_display import rebuild_eeg_data_display


def apply_changes(config_parameter_name, ui):
    if ("Sampling_rate_hz" in config_parameter_name) or (
        "Epoch_length_s" in config_parameter_name
    ):
        ui.numepo = number_of_epochs(
            ui.eeg_data.shape[1],
            ui.config[0]["Sampling_rate_hz"],
            ui.config[0]["Epoch_length_s"],
        )
        ui.stages = default_scoring(ui.config[0]["Epoch_length_s"], ui.numepo)

    if (
        ("Sampling_rate_hz" in config_parameter_name)
        or ("Epoch_length_s" in config_parameter_name)
        or ("Extension_epoch_s" in config_parameter_name)
    ):
        times_vector(ui)
        ui.this_epoch = 0

    # Channel-level settings changed (re-reference, flip, filter, display toggles) or
    # spectrogram channel / sampling rate / epoch length changed → rebuild display data
    # and recompute all derived spectral data.
    channel_settings_changed = config_parameter_name == []
    spectrogram_params_changed = (
        "Channel_for_spectogram" in config_parameter_name
        or "Sampling_rate_hz" in config_parameter_name
        or "Epoch_length_s" in config_parameter_name
    )
    if channel_settings_changed or spectrogram_params_changed:
        rebuild_eeg_data_display(ui)
        rebuild_channel_index(ui)
        recompute_derived(ui)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)

    if "Spectogram_limit_hz" in config_parameter_name:
        ui.freqsOI = freqs_of_interest(ui.freqs, ui.config)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)

    if "Spectrogram_power_limits" in config_parameter_name:
        # Fast-path: only update colorbar levels, don't redraw spectrogram
        levels = ui.config[0].get("Spectrogram_power_limits", [-1, 3])
        ui.SpectogramWidget.update_levels_only(levels)

    if "Periodogram_channel" in config_parameter_name:
        # Recompute all epoch periodograms for the new channel
        precompute_all_epoch_periodograms(ui)
        freqs, power, channel_name = compute_epoch_periodogram(ui, ui.this_epoch)
        ui.RectanglePower.update_powerline(freqs, power, channel_name)
    elif (
        "Periodogram_limit_hz" in config_parameter_name
        or "Periodogram_display_mode" in config_parameter_name
    ):
        # Fast-path: only update display trim/scale, no need to recompute
        freqs, power, channel_name = compute_epoch_periodogram(ui, ui.this_epoch)
        ui.RectanglePower.update_powerline(freqs, power, channel_name)

    # Fast-path for colorbar limit changes: no Morlet recompute, no reslice
    if "Wavelet_power_limits" in config_parameter_name and len(config_parameter_name) == 1:
        power_limits = ui.config[0].get("Wavelet_power_limits", None)
        if power_limits:
            display_mode = ui.config[0].get("Wavelet_display_mode", "Z-scored Power")
            if display_mode in power_limits:
                ui.TFWidget.update_levels_only(power_limits[display_mode])
        write_configuration(f"{ui.filename}.config.json", ui.config)
        return

    if "Wavelet_frequency_limits_hz" in config_parameter_name:
        srate = ui.config[0]["Sampling_rate_hz"]
        tf_limits = ui.config[0]["Wavelet_frequency_limits_hz"]
        min_freq = max(float(tf_limits[0]), 0.1)
        max_freq = min(float(tf_limits[1]), srate / 2 - 0.25)
        ui.tf_freqs = np.geomspace(min_freq, max_freq, 120)
        log_power = np.log10(np.maximum(ui.power, 1e-30))
        median_welch = np.median(log_power, axis=0)
        iqr_welch = np.percentile(log_power, 75, axis=0) - np.percentile(log_power, 25, axis=0)
        iqr_welch = np.maximum(iqr_welch, 1e-6)
        rms_welch = np.sqrt(np.mean(log_power ** 2, axis=0))
        rms_welch = np.maximum(rms_welch, 1e-6)
        ui.tf_norm_median = np.interp(ui.tf_freqs, ui.freqs, median_welch)
        ui.tf_norm_iqr = np.interp(ui.tf_freqs, ui.freqs, iqr_welch)
        ui.tf_norm_rms = np.interp(ui.tf_freqs, ui.freqs, rms_welch)
        median_linear_welch = np.median(ui.power, axis=0)
        median_linear_welch = np.maximum(median_linear_welch, 1e-30)
        ui.tf_norm_median_linear = np.interp(ui.tf_freqs, ui.freqs, median_linear_welch)

        # Clear the per-epoch Morlet cache since frequency range changed
        if hasattr(ui, 'tf_cache'):
            ui.tf_cache = {}

    if "Wavelet_channel" in config_parameter_name:
        # Clear cache when channel changes (raw power will differ)
        if hasattr(ui, 'tf_cache'):
            ui.tf_cache = {}

    # Apply TF panel visibility
    apply_tf_visibility(ui)

    # Redraw EEG
    redraw_gui(ui)

    # Hypnogram has it's own time scale
    if (
        ("Sampling_rate_hz" in config_parameter_name)
        or ("Epoch_length_s" in config_parameter_name)
    ):
        ui.HypnogramWidget.draw_hypnogram(ui)
        ui.stages = default_scoring(ui.config[0]["Epoch_length_s"], ui.numepo)

    # Write configuration file
    write_configuration(f"{ui.filename}.config.json", ui.config)
