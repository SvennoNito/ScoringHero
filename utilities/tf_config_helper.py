def call_tf_widget(ui):
    if not ui.config[0].get("Wavelet_panel_visible", True):
        return
    srate = ui.config[0]["Sampling_rate_hz"]
    display_mode = ui.config[0].get("Wavelet_display_mode", "Z-scored Power")
    freq_scale = ui.config[0].get("Wavelet_frequency_scale", "Logarithmic")
    freq_limits = ui.config[0].get("Wavelet_frequency_limits_hz", None)
    time_unit = ui.config[0].get("EEG_panel_time_unit", "Seconds")
    epoch_length = ui.config[0]["Epoch_length_s"]
    tf_channel_label = ui.config[0].get("Wavelet_channel", "")
    tf_channel_idx = ui.channel_name_to_idx.get(tf_channel_label, 0)
    power_limits = ui.config[0].get("Wavelet_power_limits", None)
    show_ridge = ui.config[0].get("Wavelet_show_ridge", False)
    ui.TFWidget.update_tf(ui.eeg_data_display, ui.times, ui.this_epoch, srate, ui.tf_freqs,
                          ui.tf_norm_median, ui.tf_norm_iqr, ui.tf_norm_rms, ui.tf_norm_median_linear,
                          display_mode, freq_scale, freq_limits,
                          time_unit, epoch_length, tf_channel_idx, tf_channel_label,
                          power_limits, show_ridge)
