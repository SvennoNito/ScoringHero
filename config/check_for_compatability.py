from .default_config import default_configuration
from .write_configuration import write_configuration

def check_for_compatability(configuration_settings, configuration_filename, number_of_channels, srate, channel_names):

    default_settings = default_configuration(number_of_channels, srate, channel_names)

    for unit, value in default_settings[0].items():
        if unit not in configuration_settings[0]:
            print(f"Added '{unit}' to configuration file. Default value used. Default value: {value}")
            configuration_settings[0][unit] = value

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
