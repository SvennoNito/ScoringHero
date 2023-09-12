import json


def write_configuration(configuration_filename, configuration_settings):
    with open(configuration_filename, "w") as file:
        json.dump(configuration_settings, file, indent=2)
