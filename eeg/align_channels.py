import numpy as np


def align_channels_to_config(eeg_data, channel_names, config):
    """Reorder eeg_data rows to match the channel order saved in config[1], and
    append reconstructed derived channels (e.g. re-referenced channels added via
    the config window) that are not stored as rows in the raw file.

    Shared by the primary EEG loader and the overlay-signal loader so that both
    data sets line up channel-for-channel with config[1].
    """
    non_derived_configs = [ch for ch in config[1] if not ch.get("derived", False)]
    name_to_file_idx = {name: i for i, name in enumerate(channel_names)}
    config_names = [ch["Channel_name"] for ch in non_derived_configs]
    if (len(config_names) == len(channel_names)
            and all(n in name_to_file_idx for n in config_names)):
        new_order = [name_to_file_idx[n] for n in config_names]
        eeg_data = eeg_data[new_order]

    for ch_config in config[1]:
        if ch_config.get("derived", False):
            src_name = ch_config.get("source_channel", ch_config["Channel_name"])
            src_idx = next(
                (i for i, c in enumerate(config[1])
                 if c["Channel_name"] == src_name and not c.get("derived", False)),
                None,
            )
            if src_idx is not None and src_idx < eeg_data.shape[0]:
                eeg_data = np.vstack([eeg_data, eeg_data[src_idx:src_idx + 1]])
            else:
                eeg_data = np.vstack([eeg_data, np.zeros((1, eeg_data.shape[1]))])

    return eeg_data
