def default_configuration(number_of_channels, srate = 125):
    configuration_settings      = [[] for x in range(2)]
    configuration_settings[0]   = { 
                    "Sampling_rate_hz": srate,
                    "Epoch_length_s": 30, 
                    "Distance_between_channels_muV": 25,
                    "Extension_epoch_left_s": 5,
                    "Extension_epoch_right_s": 5,
                    "Channel_index_for_spectogram": 1,
                    "Spectogram_lower_limit_hz": 0,
                    "Spectogram_upper_limit_hz": 20,
                    "Area_power_lower_limit_hz": 4 ,
                    "Area_power_upper_limit_hz": 26,
                    }
    
    configuration_settings[1] = [{
        "Channel_name": f'Channel {chan+1}',
        "Channel_color": "Black",
        "Display_on_screen": 1 if chan < 9 else 0,
        "Scaling_factor": 1
    }
    for chan in range(number_of_channels)]

    return configuration_settings  