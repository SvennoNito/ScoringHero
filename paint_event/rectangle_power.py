from scipy.signal import welch
import numpy as np
from signal_processing.trim_power import trim_power
from signal_processing.min_max_scale import min_max_scale


def rectangle_power(ui, converted_corner, converted_shape):
    # Selected sample points
    time_index = (converted_corner[0].x() <= ui.times[ui.this_epoch][0]) & (
        ui.times[ui.this_epoch][0] <= converted_corner[1].x()
    )
    samples = ui.times[ui.this_epoch][1][time_index]

    # Select channel
    numchans_visible = len(
        [counter for counter, info in enumerate(ui.config[1]) if info["Display_on_screen"]]
    )
    channel_anchors = np.array(
        [
            -ui.config[0]["Distance_between_channels_muV"] * numchans_visible * chan_counter
            for chan_counter in range(numchans_visible)
        ]
    )
    rectangle_midpoint_in_amp = (
        min(converted_corner[1].y(), converted_corner[0].y()) + converted_shape[1] / 2
    )
    channel = np.argmin(abs(channel_anchors - rectangle_midpoint_in_amp))

    # Compute power
    data = ui.eeg_data[channel][samples]
    freqs, power = welch(
        data,
        fs=ui.config[0]["Sampling_rate_hz"],
        window="hann",
        nperseg=min(len(data), 2 * ui.config[0]["Sampling_rate_hz"]),
        detrend="constant",
        return_onesided=True,
        scaling="density",
        average="mean",
    )

    # Trim to frequencies of interest
    power, freqs = trim_power(
        power,
        freqs,
        ui.config[0]["Area_power_upper_limit_hz"],
        ui.config[0]["Area_power_lower_limit_hz"],
    )

    # Scale power values between 0 and 1
    power = min_max_scale(power)
    return freqs, power
