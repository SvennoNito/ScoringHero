import numpy as np
from scipy.signal import welch
from utilities.timing_decorator import timing_decorator
from .compute_swa import compute_swa


def spectogram_to_ui(ui):
    ui.power, ui.freqs, ui.freqsOI, ui.swa = spectogram_wrapper(ui)


def spectogram_wrapper(ui):
    power, freqs = compute_spectogram(
        ui.eeg_data,
        ui.times,
        ui.config[0]["Sampling_rate_hz"],
        ui.config[0]["Channel_for_spectogram"] - 1,
        ui.config[0]["Epoch_length_s"],
    )
    freqsOI = freqsOI_ui(freqs, ui.config)
    swa = compute_swa(power, freqs)
    return power, freqs, freqsOI, swa


@timing_decorator
def compute_spectogram(eeg_data, times, srate, channel, epolen, winlen=4):
    indices_window = [
        np.arange(start, start + srate * winlen)
        for start in range(0, epolen * srate + 2 * srate, 2 * srate)
    ]
    power = np.empty((len(times), len(indices_window), int(winlen * srate / 2 + 1)))
    for i_epoch, times_indices_epoch in enumerate(times):
        indices_epoch = times_indices_epoch[1]
        for i_window, index_window in enumerate(indices_window):
            indices = indices_epoch[index_window]
            freqs, power[i_epoch, i_window, :] = welch(
                eeg_data[channel][indices],
                fs=srate,
                window="hann",
                nperseg=winlen * srate,
                detrend="constant",
                return_onesided=True,
                scaling="density",
                average="mean",
            )

    # Mean over 4s windows
    power = np.mean(power, axis=1)

    return power, freqs


def freqsOI_ui(freqs, config):
    freqsOI = freqs_of_interest_indices(
        freqs,
        config[0]["Spectogram_limit_hz"][0],
        config[0]["Spectogram_limit_hz"][1],
    )
    return freqsOI


def freqs_of_interest_indices(freqs, lower_limit, upper_limit):
    return (freqs >= lower_limit) & (freqs <= upper_limit)
