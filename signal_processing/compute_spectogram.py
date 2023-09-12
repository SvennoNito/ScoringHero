import numpy as np
from scipy.signal import welch
from utilities.timing_decorator import timing_decorator


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
