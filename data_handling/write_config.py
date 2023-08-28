import json


def write_configuration_file(configuration_filename, configuration_settings):
    with open(configuration_filename, "w") as file:
        json.dump(configuration_settings, file, indent=4)
