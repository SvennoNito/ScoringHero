import numpy as np
from edfio import read_edf as _read_edf


def load_edf(filename_prefix, scale_to_uv=False):
    file = f'{filename_prefix}.edf'
    edf = _read_edf(file)
    srate = int(edf.signals[0].sampling_frequency)
    channel_names = [s.label for s in edf.signals]
    signals = [s.data for s in edf.signals]
    max_len = max(len(s) for s in signals)
    eeg_data = np.array([
        np.pad(s, (0, max_len - len(s))) if len(s) < max_len else s
        for s in signals
    ])
    if scale_to_uv:
        eeg_data = eeg_data * 1e6
    return eeg_data, srate, channel_names
