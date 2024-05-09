from .default_config import default_configuration
from .write_configuration import write_configuration

def check_for_compatability(configuration_settings, configuration_filename, number_of_channels, srate, channel_names):

    default_settings = default_configuration(number_of_channels, srate, channel_names)

    for unit, value in default_settings[0].items():
        if unit not in configuration_settings[0]:
            print(f"Added '{unit}' to configuration file. Default value used. Default value: {value}")
            configuration_settings[0][unit] = value
    
    write_configuration(configuration_filename, configuration_settings)

    return configuration_settings
