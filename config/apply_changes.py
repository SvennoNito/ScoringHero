from .write_configuration import write_configuration
from eeg.number_of_epochs import number_of_epochs
from data_handling.default_scoring import default_scoring
from cache.ui_to_cache import ui_to_cache
from cache.write_cache import write_cache
from signal_processing.trim_power import trim_power
from signal_processing.min_max_scale import min_max_scale
from signal_processing.build_times_vector import build_times_vector
from signal_processing.compute_spectogram import freqsOI_ui, spectogram_to_ui
from utilities.redraw_gui import redraw_gui


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
        build_times_vector(ui)

    if (
        ("Channel_for_spectogram" in config_parameter_name)
        or ("Sampling_rate_hz" in config_parameter_name)
        or ("Epoch_length_s" in config_parameter_name)
    ):
        spectogram_to_ui(ui)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)
        write_cache(ui, ui_to_cache(ui))

    if "Spectogram_limit_hz" in config_parameter_name:
        ui.freqsOI = freqsOI_ui(ui.freqs, ui.config)
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

    # Redraw EEG
    redraw_gui(ui)

    # Write configuration file
    write_configuration(f"{ui.filename}.config.json", ui.config)
