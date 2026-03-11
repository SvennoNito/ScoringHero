import numpy as np
from events.draw_event_in_this_epoch import draw_event_in_this_epoch


def redraw_gui(ui):
    # Redraw EEG data
    ui.SignalWidget.draw_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)

    # Update display text
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)

    # Draw time-frequency panel
    srate = ui.config[0]["Sampling_rate_hz"]
    max_freq = min(45.0, srate / 2 - 0.25)
    tf_freqs = np.arange(0.25, max_freq + 0.25, 0.25)
    ui.TFWidget.draw_tf(ui.eeg_data, ui.times, ui.this_epoch, srate, tf_freqs,
                        ui.tf_norm_median, ui.tf_norm_iqr)

    # Draw annotations
    for container in ui.AnnotationContainer:
        draw_event_in_this_epoch(ui, container)
