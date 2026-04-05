from .default_config import default_configuration
from .write_configuration import write_configuration

def check_for_compatability(configuration_settings, configuration_filename, number_of_channels, srate, channel_names):

    default_settings = default_configuration(number_of_channels, srate, channel_names)

    for unit, value in default_settings[0].items():
        if unit not in configuration_settings[0]:
            print(f"Added '{unit}' to configuration file. Default value used. Default value: {value}")
            configuration_settings[0][unit] = value

    # Separate derived channels (added via re-reference) from original channels.
    # Derived channels are not stored in the EEG file so they must not be counted
    # against number_of_channels when reconciling the channel list.
    non_derived = [ch for ch in configuration_settings[1] if not ch.get("derived", False)]
    derived     = [ch for ch in configuration_settings[1] if ch.get("derived", False)]

    # Fill missing keys for non-derived channels
    for i, (chan_settings, default_chan) in enumerate(zip(non_derived, default_settings[1])):
        for key, value in default_chan.items():
            if key not in chan_settings:
                print(f"Added '{key}' to channel {i+1} in configuration file. Default value used.")
                chan_settings[key] = value

    # Fill missing keys for derived channels (use first default entry as template)
    if default_settings[1]:
        default_template = default_settings[1][0]
        for chan_settings in derived:
            for key, value in default_template.items():
                if key not in chan_settings:
                    chan_settings[key] = value

    # Reconcile non-derived channel count only
    saved_non_derived_n = len(non_derived)
    if saved_non_derived_n > number_of_channels:
        non_derived = non_derived[:number_of_channels]
    elif saved_non_derived_n < number_of_channels:
        for i in range(saved_non_derived_n, number_of_channels):
            non_derived.append(default_settings[1][i])

    # Derived channels are appended after the original channels
    configuration_settings[1] = non_derived + derived

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
