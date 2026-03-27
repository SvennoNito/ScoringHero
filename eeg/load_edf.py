import numpy as np
from edfio import read_edf as _read_edf


def load_edf(filename_prefix, scale_to_uv=False):
    file = f'{filename_prefix}.edf'
    edf = _read_edf(file)
    srate = int(edf.signals[0].sampling_frequency)
    channel_names = [s.label for s in edf.signals]
    eeg_data = np.array([s.data for s in edf.signals])
    if scale_to_uv:
        eeg_data = eeg_data * 1e6
    return eeg_data, srate, channel_names
