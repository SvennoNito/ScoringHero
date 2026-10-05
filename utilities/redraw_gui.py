from events.draw_event_in_this_epoch import draw_event_in_this_epoch
from signal_processing.compute_epoch_periodogram import compute_epoch_periodogram
from utilities.tf_config_helper import call_tf_widget
from utilities.overlay_state import get_overlay_signal_for_display


def redraw_all(ui):
    """Full redraw after the displayed signal or derived data were rebuilt (filtering,
    configuration rebuild): spectrogram, hypnogram (stages, events, SWA), periodogram,
    then signal panel, text, TF panel and annotations via redraw_gui.
    Expects ui.eeg_data_display and the derived data (ui.power, ...) to be up to date.
    """
    ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)
    ui.HypnogramWidget.draw_hypnogram(ui)
    ui.SpectogramWidget.update_epoch_indicator(ui.this_epoch)
    ui.HypnogramWidget.update_epoch_indicator(ui.this_epoch)

    freqs, power, channel_name = compute_epoch_periodogram(ui, ui.this_epoch)
    ui.RectanglePower.update_powerline(freqs, power, channel_name)

    redraw_gui(ui)


def redraw_gui(ui):
    # Redraw EEG data
    ui.SignalWidget.draw_signal(ui.config, ui.eeg_data_display, ui.times, ui.this_epoch,
                                 get_overlay_signal_for_display(ui))

    # Update display text
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)

    # Draw time-frequency panel
    call_tf_widget(ui)

    # Draw annotations
    for container in ui.AnnotationContainer:
        draw_event_in_this_epoch(ui, container)
