from signal_processing.trim_power import trim_power
from signal_processing.min_max_scale import min_max_scale
from events.draw_event_in_this_epoch import draw_event_in_this_epoch


def refresh_gui(ui):
    # Update EEG signal
    ui.SignalWidget.update_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)

    # Update display text
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)

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
    power, freqs = trim_power(
        ui.power[ui.this_epoch],
        ui.freqs,
        ui.config[0]["Periodogram_limit_hz"][0],
        ui.config[0]["Periodogram_limit_hz"][1],
    )
    power = min_max_scale(power)
    ui.RectanglePower.update_powerline(freqs, power)

    # Update time-frequency panel
    srate = ui.config[0]["Sampling_rate_hz"]
    display_mode = ui.config[0].get("Wavelet_display_mode", "Z-scored Power")
    freq_scale = ui.config[0].get("Wavelet_frequency_scale", "Logarithmic")
    freq_limits = ui.config[0].get("Wavelet_frequency_limits_hz", None)
    time_unit = ui.config[0].get("EEG_panel_time_unit", "Seconds")
    epoch_length = ui.config[0]["Epoch_length_s"]
    tf_channel_label = ui.config[0].get("Wavelet_channel", "")
    channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
    tf_channel_idx = channel_labels.index(tf_channel_label) if tf_channel_label in channel_labels else 0
    ui.TFWidget.update_tf(ui.eeg_data, ui.times, ui.this_epoch, srate, ui.tf_freqs,
                          ui.tf_norm_median, ui.tf_norm_iqr, ui.tf_norm_rms, display_mode, freq_scale, freq_limits,
                          time_unit, epoch_length, tf_channel_idx, tf_channel_label)

    # Draw annotations
    for container in ui.AnnotationContainer:
        draw_event_in_this_epoch(ui, container)
