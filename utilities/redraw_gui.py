from events.draw_event_in_this_epoch import draw_event_in_this_epoch


def redraw_gui(ui):
    # Redraw EEG data
    ui.SignalWidget.draw_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)

    # Update display text
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)

    # Draw time-frequency panel
    srate = ui.config[0]["Sampling_rate_hz"]
    display_mode = ui.config[0].get("Wavelet_display_mode", "Z-scored Power")
    freq_scale = ui.config[0].get("Wavelet_frequency_scale", "Logarithmic")
    freq_limits = ui.config[0].get("Wavelet_frequency_limits_hz", None)
    time_unit = ui.config[0].get("EEG_panel_time_unit", "Seconds")
    epoch_length = ui.config[0]["Epoch_length_s"]
    tf_channel_label = ui.config[0].get("Wavelet_channel", "")
    channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
    tf_channel_idx = channel_labels.index(tf_channel_label) if tf_channel_label in channel_labels else 0
    power_limits = ui.config[0].get("Wavelet_power_limits", None)
    ui.TFWidget.draw_tf(ui.eeg_data, ui.times, ui.this_epoch, srate, ui.tf_freqs,
                        ui.tf_norm_median, ui.tf_norm_iqr, ui.tf_norm_rms, ui.tf_norm_median_linear,
                        display_mode, freq_scale, freq_limits,
                        time_unit, epoch_length, tf_channel_idx, tf_channel_label,
                        power_limits)

    # Draw annotations
    for container in ui.AnnotationContainer:
        draw_event_in_this_epoch(ui, container)
