def default_configuration(number_of_channels, srate, channel_names):
    configuration_settings = [[] for x in range(2)]
    configuration_settings[0] = {
        "Sampling_rate_hz": srate,
        "Epoch_length_s": 30,
        "Distance_between_channels_muV": 25,
        "Reference_amplitude_line_muV": 37.5,
        "Channel_for_spectogram": channel_names[0] if len(channel_names) > 0 else "Channel 1",
        "Extension_epoch_s": [5, 5],
        "Spectogram_limit_hz": [0, 45],
        "Periodogram_limit_hz": [4, 45],
        "EEG_panel_time_unit": "Seconds",
        "Wavelet_display_mode": "dB (median baseline)",
        "Wavelet_frequency_scale": "Linear",
        "Wavelet_frequency_limits_hz": [0, 45],
        "Wavelet_channel": channel_names[0] if len(channel_names) > 0 else "Channel 1",
        "Wavelet_panel_visible": True,
        "Spectrogram_power_limits": [-1, 3],
        "Wavelet_power_limits": {
            "Raw Power": [-1, 3],
            "L2-Normalized Power": [-1, 3],
            "Z-Standardized Power": [-3, 3],
            "dB (median baseline)": [0, 20],
        },
        "Stack_channels": False,
        "Robust_z_standardize": False,
    }

    configuration_settings[1] = [
        {
            "Channel_name": f"Channel {chan+1}",
            "Channel_color": "Black",
            "Display_on_screen": 1 if chan < 9 else 0,
            "Scaling_factor": 100,
            "Vertical_shift": 0,
        }
        for chan in range(number_of_channels)
    ]

    if number_of_channels == 9:
        configuration_settings[1][1]["Display_on_screen"] = 0
        configuration_settings[1][3]["Display_on_screen"] = 0
        configuration_settings[1][5]["Display_on_screen"] = 0

    if len(channel_names) > 0:
        for row, channel_name in enumerate(channel_names):
            configuration_settings[1][row]["Channel_name"] = channel_name
            name_upper = channel_name.upper()
            if "EOG" in name_upper:
                configuration_settings[1][row]["Channel_color"] = "Blue"
            elif "ECG" in name_upper:
                configuration_settings[1][row]["Channel_color"] = "Magenta"
            elif "EMG" in name_upper:
                configuration_settings[1][row]["Channel_color"] = "Orange"

    return configuration_settings
