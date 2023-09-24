def default_configuration(number_of_channels, srate, channel_names):
    configuration_settings = [[] for x in range(2)]
    configuration_settings[0] = {
        "Sampling_rate_hz": srate,
        "Epoch_length_s": 30,
        "Distance_between_channels_muV": 25,
        "Channel_for_spectogram": 1,
        "Extension_epoch_s": [5, 5],
        "Spectogram_limit_hz": [0, 20],
        "Periodogram_limit_hz": [4, 26],
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
        configuration_settings[1][6]["Channel_color"] = "Blue"
        configuration_settings[1][7]["Channel_color"] = "Blue"
        configuration_settings[1][8]["Channel_color"] = "Magenta"

    if len(channel_names) > 0:
        for row, channel_name in enumerate(channel_names):
            configuration_settings[1][row]["Channel_name"] = channel_name

    return configuration_settings
