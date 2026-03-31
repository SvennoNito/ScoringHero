from .default_config import default_configuration
from .write_configuration import write_configuration

def check_for_compatability(configuration_settings, configuration_filename, number_of_channels, srate, channel_names):

    default_settings = default_configuration(number_of_channels, srate, channel_names)

    for unit, value in default_settings[0].items():
        if unit not in configuration_settings[0]:
            print(f"Added '{unit}' to configuration file. Default value used. Default value: {value}")
            configuration_settings[0][unit] = value

    for i, (chan_settings, default_chan) in enumerate(zip(configuration_settings[1], default_settings[1])):
        for key, value in default_chan.items():
            if key not in chan_settings:
                print(f"Added '{key}' to channel {i+1} in configuration file. Default value used.")
                chan_settings[key] = value

    # Migrate Channel_for_spectogram from legacy integer (1-based) to channel label string
    if isinstance(configuration_settings[0].get("Channel_for_spectogram"), int):
        idx = configuration_settings[0]["Channel_for_spectogram"] - 1
        if 0 <= idx < len(channel_names):
            configuration_settings[0]["Channel_for_spectogram"] = channel_names[idx]
        elif len(channel_names) > 0:
            configuration_settings[0]["Channel_for_spectogram"] = channel_names[0]
        else:
            configuration_settings[0]["Channel_for_spectogram"] = "Channel 1"

    write_configuration(configuration_filename, configuration_settings)

    return configuration_settings
