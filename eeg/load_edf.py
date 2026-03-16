import numpy as np
import pyedflib

def load_edf(filename_prefix):
    file = f'{filename_prefix}.edf'
    with pyedflib.EdfReader(file) as f:
        srate         = int(f.getSampleFrequency(0))
        channel_names = f.getSignalLabels()
        units         = [f.getPhysicalDimension(i) for i in range(f.signals_in_file)]
        eeg_data      = np.array([f.readSignal(i) for i in range(f.signals_in_file)])
    for ch, unit in zip(channel_names, units):
        print(f"Channel: {ch}, Unit: {unit}")
    print(f"Min amplitude: {eeg_data[0].min()}, Max amplitude: {eeg_data[0].max()}")
    return eeg_data, srate, channel_names
