from scipy.signal import welch
from scipy.ndimage import uniform_filter1d
import numpy as np
from .trim_power import trim_power
from .min_max_scale import min_max_scale


def precompute_all_epoch_periodograms(ui):
    """Precompute Welch periodograms for all epochs on the configured periodogram channel.

    Stores raw (untrimmed) power and frequencies in ui.epoch_periodogram_power and
    ui.epoch_periodogram_freqs for fast lookup during navigation.

    Called from recompute_derived() and apply_changes() when periodogram settings change.
    """
    channel_names = [ch["Channel_name"] for ch in ui.config[1]]
    periodogram_channel_name = ui.config[0].get(
        "Periodogram_channel", channel_names[0] if channel_names else ""
    )
    channel_idx = ui.channel_name_to_idx.get(periodogram_channel_name, 0)

    signal = ui.eeg_data_display[channel_idx, :]
    srate = int(ui.config[0]["Sampling_rate_hz"])

    power_list = []
    freqs = None

    for epoch_idx in range(ui.numepo):
        _, epoch_indices, _ = ui.times[epoch_idx]
        epoch_signal = signal[epoch_indices].astype(float)

        freqs_epoch, power_epoch = welch(
            epoch_signal,
            fs=srate,
            window="hann",
            nperseg=min(len(epoch_signal), 2 * srate),
            detrend="constant",
            return_onesided=True,
            scaling="density",
            average="mean",
        )

        if freqs is None:
            freqs = freqs_epoch
        power_list.append(power_epoch)

    ui.epoch_periodogram_freqs = freqs  # (n_freqs,)
    ui.epoch_periodogram_power = np.array(power_list)  # (n_epochs, n_freqs)


def compute_epoch_periodogram(ui, epoch_idx):
    """Return the periodogram for a given epoch using cached power and display-mode trim/scale.

    Looks up precomputed power in ui.epoch_periodogram_power[epoch_idx] and applies
    display-mode trim and scaling transformations.
    """
    channel_names = [ch["Channel_name"] for ch in ui.config[1]]
    periodogram_channel_name = ui.config[0].get(
        "Periodogram_channel", channel_names[0] if channel_names else ""
    )

    # Look up precomputed raw power from cache
    freqs = ui.epoch_periodogram_freqs
    power = ui.epoch_periodogram_power[epoch_idx].copy()

    # Apply trim to configured frequency limits
    power, freqs = trim_power(
        power,
        freqs,
        ui.config[0]["Periodogram_limit_hz"][0],
        ui.config[0]["Periodogram_limit_hz"][1],
    )

    # Apply display-mode scaling/transform
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
