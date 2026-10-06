import os, json
from .default_config import default_configuration
from .write_configuration import write_configuration
from .check_for_compatability import check_for_compatability
from .channel_template import load_channel_template
from .channel_settings import merge_template

def load_configuration(configuration_filename, number_of_channels=6, srate=125, channel_names=[], app_path=None, units=None):
    if os.path.exists(configuration_filename):
        with open(configuration_filename, "r") as file:
            configuration_settings = json.load(file)

        # Check whether all configuration items are present
        configuration_settings =  check_for_compatability(configuration_settings, configuration_filename, number_of_channels, srate, channel_names, units)

    else:
        configuration_settings = default_configuration(number_of_channels, srate, channel_names, units)

        # First time this recording is opened: inherit re-reference, filter, flip
        # and display settings from the last-edited recording's channel config,
        # for any channel names the two recordings share.
        template = load_channel_template(app_path)
        if template:
            configuration_settings[1] = merge_template(configuration_settings[1], template)

        write_configuration(configuration_filename, configuration_settings)

    return configuration_settings
