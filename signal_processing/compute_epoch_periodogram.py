from scipy.signal import welch
from scipy.ndimage import uniform_filter1d
import numpy as np
from .trim_power import trim_power
from .min_max_scale import min_max_scale


def compute_epoch_periodogram(ui, epoch_idx):
    """Compute the periodogram for a given epoch using the configured periodogram channel and display mode."""
    channel_names = [ch["Channel_name"] for ch in ui.config[1]]
    periodogram_channel_name = ui.config[0].get(
        "Periodogram_channel", channel_names[0] if channel_names else ""
    )
    channel_idx = (
        channel_names.index(periodogram_channel_name)
        if periodogram_channel_name in channel_names
        else 0
    )

    _, epoch_indices, _ = ui.times[epoch_idx]
    data = ui.eeg_data_display[channel_idx][epoch_indices].astype(float)

    srate = int(ui.config[0]["Sampling_rate_hz"])
    freqs, power = welch(
        data,
        fs=srate,
        window="hann",
        nperseg=min(len(data), 2 * srate),
        detrend="constant",
        return_onesided=True,
        scaling="density",
        average="mean",
    )

    power, freqs = trim_power(
        power,
        freqs,
        ui.config[0]["Periodogram_limit_hz"][0],
        ui.config[0]["Periodogram_limit_hz"][1],
    )

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

    return freqs, power, periodogram_channel_name
