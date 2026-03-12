import numpy as np
from .write_configuration import write_configuration
from eeg.number_of_epochs import number_of_epochs
from scoring.default_scoring import default_scoring
from cache.ui_to_cache import ui_to_cache
from cache.write_cache import write_cache
from signal_processing.trim_power import trim_power
from signal_processing.min_max_scale import min_max_scale
from signal_processing.times_vector import times_vector
from signal_processing.spectogram_to_ui import spectogram_to_ui
from signal_processing.freqs_of_interest import freqs_of_interest
from utilities.redraw_gui import redraw_gui
from utilities.apply_tf_visibility import apply_tf_visibility
from scoring.default_scoring import default_scoring


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

    if (
        ("Channel_for_spectogram" in config_parameter_name)
        or ("Sampling_rate_hz" in config_parameter_name)
        or ("Epoch_length_s" in config_parameter_name)
    ):
        ui.power, ui.freqs, ui.freqsOI, ui.swa = spectogram_to_ui(ui)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)
        write_cache(ui, ui_to_cache(ui))

    if "Spectogram_limit_hz" in config_parameter_name:
        ui.freqsOI = freqs_of_interest(ui.freqs, ui.config)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)
        write_cache(ui, ui_to_cache(ui))

    if "Periodogram_limit_hz" in config_parameter_name:
        power, freqs = trim_power(
            ui.power[ui.this_epoch],
            ui.freqs,
            ui.config[0]["Periodogram_limit_hz"][0],
            ui.config[0]["Periodogram_limit_hz"][1],
        )
        power = min_max_scale(power)
        ui.RectanglePower.update_powerline(freqs, power)

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
