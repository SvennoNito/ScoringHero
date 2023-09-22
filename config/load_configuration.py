import os, json
from .default_config import default_configuration
from .write_configuration import write_configuration


def load_configuration(configuration_filename, number_of_channels=6, srate=125):
    if os.path.exists(configuration_filename):
        with open(configuration_filename, "r") as file:
            configuration_settings = json.load(file)

    else:
        configuration_settings = default_configuration(number_of_channels, srate)
        write_configuration(configuration_filename, configuration_settings)

    return configuration_settings
