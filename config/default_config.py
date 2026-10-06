from .channel_settings import default_channels


def default_configuration(number_of_signals, srate, channel_names, units=None):
    # number_of_signals = number of signals in the file. units = per-signal
    # unit strings; None means unknown (treated as voltage).
    configuration_settings = [[] for x in range(2)]
    configuration_settings[0] = {
        "Sampling_rate_hz": srate,
        "Epoch_length_s": 30,
        "Distance_between_channels_muV": 25,
        "Reference_amplitude_line_muV": 37.5,
        "Channel_for_spectogram": channel_names[0] if len(channel_names) > 0 else "Channel 1",
        "Extension_epoch_s": [5, 5],
        "Spectogram_limit_hz": [0, 45],
        "Periodogram_limit_hz": [4, 45],
        "Periodogram_channel": channel_names[0] if len(channel_names) > 0 else "Channel 1",
        "Periodogram_display_mode": "1/f Removed",
        "EEG_panel_time_unit": "Seconds",
        "Recording_start_time": "00:00",
        "Wavelet_display_mode": "dB (median baseline)",
        "Wavelet_frequency_scale": "Linear",
        "Wavelet_frequency_limits_hz": [0, 45],
        "Wavelet_channel": channel_names[0] if len(channel_names) > 0 else "Channel 1",
        "Wavelet_panel_visible": True,
        "Wavelet_show_ridge": False,
        "Spectrogram_power_limits": [-1, 3],
        "Wavelet_power_limits": {
            "Raw Power": [-1, 3],
            "L2-Normalized Power": [-1, 3],
            "Z-Standardized Power": [-3, 3],
            "dB (median baseline)": [0, 20],
        },
        "Stack_channels": False,
        "Robust_z_standardize": False,
    }

    configuration_settings[1] = default_channels(number_of_signals, channel_names, units)

    return configuration_settings
