from signal_processing.compute_epoch_periodogram import compute_epoch_periodogram
from events.draw_event_in_this_epoch import draw_event_in_this_epoch
from utilities.tf_config_helper import call_tf_widget


def refresh_gui(ui):
    # Update EEG signal
    ui.SignalWidget.update_signal(ui.config, ui.eeg_data_display, ui.times, ui.this_epoch)

    # Update display text
    stages_ref = getattr(ui, "stages_ref", None)
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages, stages_ref)

    # Update epoch indicator lines
    ui.SpectogramWidget.update_epoch_indicator(ui.this_epoch)
    ui.HypnogramWidget.update_epoch_indicator(ui.this_epoch)

    # Remove green rectangles
    ui.PaintEventWidget.reset()

    # Remove rectangle size text
    ui.SignalWidget.text_amplitude_box.setText("")
    ui.SignalWidget.text_amplitude_signal.setText("")
    ui.SignalWidget.text_period.setText("")

    # Show power line of epoch
    freqs, power, channel_name = compute_epoch_periodogram(ui, ui.this_epoch)
    ui.RectanglePower.update_powerline(freqs, power, channel_name)

    # Update time-frequency panel
    call_tf_widget(ui)

    # Draw annotations
    for container in ui.AnnotationContainer:
        draw_event_in_this_epoch(ui, container)

    # Update export menu state based on scoring
    _update_export_menu_state(ui)


def _update_export_menu_state(ui):
    """Enable/disable sleep report export based on scoring availability."""
    has_scores = ui.stages and any(stage.get("digit") is not None for stage in ui.stages)
    if hasattr(ui, "action_export_sleep_report"):
        ui.action_export_sleep_report.setEnabled(has_scores)
