from events.draw_event_in_this_epoch import draw_event_in_this_epoch
from utilities.tf_config_helper import call_tf_widget
from utilities.overlay_state import get_overlay_signal_for_display


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
