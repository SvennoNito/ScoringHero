from .compute_swa import compute_swa
from .freqs_of_interest import freqs_of_interest
from .compute_spectogram import compute_spectogram


def spectogram_to_ui(ui):
    power, freqs = compute_spectogram(
        ui.eeg_data,
        ui.times,
        ui.config[0]["Sampling_rate_hz"],
        ui.config[0]["Channel_for_spectogram"] - 1,
        ui.config[0]["Epoch_length_s"],
    )
    freqsOI = freqs_of_interest(freqs, ui.config)
    swa = compute_swa(power, freqs)
    return power, freqs, freqsOI, swa


# Usage: ui.power, ui.freqs, ui.freqsOI, ui.swa = spectogram_wrapper(ui)
