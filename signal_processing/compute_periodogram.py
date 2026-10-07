from scipy.signal import welch
from scipy.ndimage import uniform_filter1d
import numpy as np

from signal_processing.trim_power import trim_power
from signal_processing.min_max_scale import min_max_scale


def compute_periodogram(ui, data, times):

    # Compute power
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

    # Apply display mode
    display_mode = ui.config[0].get("Periodogram_display_mode", "1/f Removed")
    if display_mode == "1/f Removed":
        power_smooth = uniform_filter1d(power, size=20)
        power = power / power_smooth
        power = min_max_scale(power)
    elif display_mode == "dB":
        power = 10 * np.log10(np.maximum(power, 1e-30))
        power = min_max_scale(power)
    else:  # Raw Power
        power = min_max_scale(power)

    # Also store selected data in ui
    ui.PaintEventWidget.selected_data = (data, times)
    return freqs, power
