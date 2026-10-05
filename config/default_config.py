from eeg.units import is_voltage_unit, normalize_unit

DEFAULT_LINE_WIDTH = 2.0  # px, per-channel trace width on the signal panel


def default_scaling_factor(number_of_signals):
    """Default Scaling_factor (%) by number of signals in the file."""
    if number_of_signals <= 3:
        return 50
    if number_of_signals <= 7:
        return 75
    return 100


def default_subtract_median(unit):
    """True for a known non-voltage unit (e.g. 'g'); False for voltage or unknown."""
    return normalize_unit(unit) is not None and not is_voltage_unit(unit)


# Channel keys whose default depends on the signal (e.g. its unit). A channel
# without a signal of its own (derived channel) that lacks such a key in an older
# configuration file gets this neutral value instead.
LEGACY_NEUTRAL_DEFAULTS = {"Subtract_median": False}


def default_configuration(number_of_signals, srate, channel_names, units=None):
    # number_of_signals = number of signals in the file. units = per-signal
    # unit strings; None means unknown (treated as voltage).
    scaling_factor = default_scaling_factor(number_of_signals)
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

    configuration_settings[1] = [
        {
            "Channel_name": f"Channel {chan+1}",
            "Channel_color": "Black",
            "Display_on_screen": 1 if chan < 9 else 0,
            "Scaling_factor": scaling_factor,
            "Vertical_shift": 0,
            "Re_reference": "None",
            "Flip_polarity": False,
            "Subtract_median": default_subtract_median(units[chan] if units is not None and chan < len(units) else None),
            "Line_width": DEFAULT_LINE_WIDTH,
            "Filter_hp_enabled": False,
            "Filter_hp_cutoff": 0.3,
            "Filter_hp_order": 4,
            "Filter_lp_enabled": False,
            "Filter_lp_cutoff": 50.0,
            "Filter_lp_order": 4,
            "Filter_notch_enabled": False,
            "Filter_notch_cutoff": 50.0,
            "Filter_notch_order": 4,
        }
        for chan in range(number_of_signals)
    ]

    if number_of_signals == 9:
        configuration_settings[1][1]["Display_on_screen"] = 0
        configuration_settings[1][3]["Display_on_screen"] = 0
        configuration_settings[1][5]["Display_on_screen"] = 0

    if len(channel_names) > 0:
        for row, channel_name in enumerate(channel_names):
            configuration_settings[1][row]["Channel_name"] = channel_name
            name_upper = channel_name.upper()
            if "EOG" in name_upper:
                configuration_settings[1][row]["Channel_color"] = "Blue"
            elif "ECG" in name_upper:
                configuration_settings[1][row]["Channel_color"] = "Magenta"
            elif "EMG" in name_upper:
                configuration_settings[1][row]["Channel_color"] = "Orange"

    return configuration_settings
