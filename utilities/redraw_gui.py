from events.draw_event_in_this_epoch import draw_event_in_this_epoch


def redraw_gui(ui):
    # Redraw EEG data
    ui.SignalWidget.draw_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)

    # Update display text
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)

    # Draw time-frequency panel
    srate = ui.config[0]["Sampling_rate_hz"]
    display_mode = ui.config[0].get("TF_display_mode", "Z-scored Power")
    freq_scale = ui.config[0].get("TF_frequency_scale", "Logarithmic")
    freq_limits = ui.config[0].get("TF_frequency_limits_hz", None)
    y_axis_scale = ui.config[0].get("TF_y_axis_scale", "Logarithmic")
    y_axis_limits = ui.config[0].get("TF_y_axis_limits", None)
    time_unit = ui.config[0].get("EEG_panel_time_unit", "Seconds")
    epoch_length = ui.config[0]["Epoch_length_s"]
    tf_channel_label = ui.config[0].get("TF_channel", "")
    channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
    tf_channel_idx = channel_labels.index(tf_channel_label) if tf_channel_label in channel_labels else 0
    ui.TFWidget.draw_tf(ui.eeg_data, ui.times, ui.this_epoch, srate, ui.tf_freqs,
                        ui.tf_norm_median, ui.tf_norm_iqr, ui.tf_norm_rms, display_mode, freq_scale, freq_limits,
                        y_axis_scale, y_axis_limits, time_unit, epoch_length, tf_channel_idx)

    # Draw annotations
    for container in ui.AnnotationContainer:
        draw_event_in_this_epoch(ui, container)
