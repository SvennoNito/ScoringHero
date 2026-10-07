from .write_configuration import save_configuration
from eeg.displayed_signal import settings_changed
from eeg.number_of_epochs import number_of_epochs
from scoring.scoring_import_comparison import clear_comparison
from scoring_model.scoring import Scoring
from signal_processing.compute_epoch_periodogram import compute_epoch_periodogram
from signal_processing.times_vector import times_vector
from signal_processing.freqs_of_interest import freqs_of_interest
from utilities.apply_tf_visibility import apply_tf_visibility


def apply_changes(config_parameter_name, ui, channels_changed=False):
    """Apply changed general settings (config_parameter_name: changed keys of
    ui.config[0]). channels_changed=True: the channel list changed as well (channel
    added or deleted), so the displayed signal must be brought up to date."""
    if ("Sampling_rate_hz" in config_parameter_name) or (
        "Epoch_length_s" in config_parameter_name
    ):
        ui.numepo = number_of_epochs(
            ui.eeg_data.shape[1],
            ui.config[0]["Sampling_rate_hz"],
            ui.config[0]["Epoch_length_s"],
        )
        ui.scoring = Scoring(ui.numepo, ui.config[0]["Epoch_length_s"])
        clear_comparison(ui)

    if (
        ("Sampling_rate_hz" in config_parameter_name)
        or ("Epoch_length_s" in config_parameter_name)
        or ("Extension_epoch_s" in config_parameter_name)
    ):
        times_vector(ui)
        ui.this_epoch = 0

    # Fast-path for colorbar limit changes: no Morlet recompute, no reslice
    if config_parameter_name == ["Wavelet_power_limits"] and not channels_changed:
        power_limits = ui.config[0].get("Wavelet_power_limits", None)
        if power_limits:
            display_mode = ui.config[0].get("Wavelet_display_mode", "Z-scored Power")
            if display_mode in power_limits:
                ui.TFWidget.update_levels_only(power_limits[display_mode])
        save_configuration(ui)
        return

    settings_changed(ui, lambda: _finish_changes(config_parameter_name, ui))


def _finish_changes(config_parameter_name, ui):
    """Display-only general settings that need no rebuild or recompute."""
    if "Spectogram_limit_hz" in config_parameter_name:
        ui.freqsOI = freqs_of_interest(ui.freqs, ui.config)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)

    if "Spectrogram_power_limits" in config_parameter_name:
        # Fast-path: only update colorbar levels, don't redraw spectrogram
        levels = ui.config[0].get("Spectrogram_power_limits", [-1, 3])
        ui.SpectogramWidget.update_levels_only(levels)

    if (
        "Periodogram_limit_hz" in config_parameter_name
        or "Periodogram_display_mode" in config_parameter_name
    ):
        # Fast-path: only update display trim/scale, no need to recompute
        freqs, power, channel_name = compute_epoch_periodogram(ui, ui.this_epoch)
        ui.RectanglePower.update_powerline(freqs, power, channel_name)

    # Apply TF panel visibility
    apply_tf_visibility(ui)

    # Update time axis labels on all panels when time unit or start time changes
    if (
        "EEG_panel_time_unit" in config_parameter_name
        or "Recording_start_time" in config_parameter_name
    ):
        ui.SpectogramWidget.update_time_axis_only(ui.config)
        ui.HypnogramWidget.update_time_axis(ui)
