from .compute_swa import compute_swa
from .freqs_of_interest import freqs_of_interest
from .compute_spectogram import compute_spectogram


def spectogram_to_ui(ui):
    channel_label = ui.config[0]["Channel_for_spectogram"]
    channel_names = [ch["Channel_name"] for ch in ui.config[1]]
    channel_idx = channel_names.index(channel_label) if channel_label in channel_names else 0
    power, freqs = compute_spectogram(
        ui.eeg_data_display,
        ui.times,
        ui.config[0]["Sampling_rate_hz"],
        channel_idx,
        ui.config[0]["Epoch_length_s"],
    )
    freqsOI = freqs_of_interest(freqs, ui.config)
    swa = compute_swa(power, freqs)
    return power, freqs, freqsOI, swa


# Usage: ui.power, ui.freqs, ui.freqsOI, ui.swa = spectogram_wrapper(ui)
