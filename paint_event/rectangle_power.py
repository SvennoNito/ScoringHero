from scipy.signal import welch
import numpy as np
from .selected_samples import selected_samples
from .selected_channel import selected_channel
from signal_processing.trim_power import trim_power
from signal_processing.min_max_scale import min_max_scale


def rectangle_power(ui, converted_corner, converted_shape):
    
    # Selected sample points
    samples, times = selected_samples(ui.times, ui.this_epoch, converted_corner)

    # Select channel
    channel = selected_channel(ui.config, converted_corner, converted_shape)

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
        ui.config[0]["Periodogram_limit_hz"][0],
        ui.config[0]["Periodogram_limit_hz"][1],
    )

    # Scale power values between 0 and 1
    power = min_max_scale(power)

    # Also store selected data in ui
    ui.PaintEventWidget.selected_data = (data, times)
    return freqs, power
