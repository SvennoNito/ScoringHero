import os, json
from .default_config import default_configuration
from .write_config import write_configuration_file

def load_configuration(configuration_filename, number_of_channels=6):
    if os.path.exists(configuration_filename):
        with open(configuration_filename, "r") as file:
            configuration_settings = json.load(file)

    else:
        configuration_settings = default_configuration(number_of_channels)
        write_configuration_file(configuration_filename, configuration_settings)
        
    return configuration_settings