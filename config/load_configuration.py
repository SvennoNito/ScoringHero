import os, json
from .default_config import default_configuration
from .write_configuration import write_configuration
from .check_for_compatability import check_for_compatability

def load_configuration(configuration_filename, number_of_channels=6, srate=125, channel_names=[]):
    if os.path.exists(configuration_filename):
        with open(configuration_filename, "r") as file:
            configuration_settings = json.load(file)

        # Check whether all configuration items are present
        configuration_settings =  check_for_compatability(configuration_settings, configuration_filename, number_of_channels, srate, channel_names)

    else:
        configuration_settings = default_configuration(number_of_channels, srate, channel_names)
        write_configuration(configuration_filename, configuration_settings)

    return configuration_settings
