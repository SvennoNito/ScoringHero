import json

from .channel_template import save_channel_template


def write_configuration(configuration_filename, configuration_settings):
    with open(configuration_filename, "w") as file:
        json.dump(configuration_settings, file, indent=2)


def save_configuration(ui):
    """Write ui.config to this recording's own config.json, and also refresh the
    global channel template (config[1]) from it, so the next newly-opened
    recording that has no config.json of its own inherits the same re-reference,
    filter, flip and display settings for any channel names it shares."""
    write_configuration(f"{ui.filename}.config.json", ui.config)
    save_channel_template(getattr(ui, "app_path", None), ui.config)
