import h5py
from scipy import io
import numpy as np
import os

def load_eeglab(filename_prefix):
    # Check if the file is a MATLAB v7.3+ file (HDF5-based)
    try:
        with h5py.File(f'{filename_prefix}.mat', 'r') as loaded_file:
            eeg_data    = loaded_file["EEG"]["data"][:]
            srate       = loaded_file["EEG"]["srate"][0][0]
            chanlocs    = np.array(loaded_file["EEG"]["chanlocs"]['labels']).flatten()

            channel_names = []
            for chanloc in chanlocs:
                referred_data = loaded_file[chanloc][()]  # Follow the reference to get the data
                channel_names.append(referred_data.tobytes().decode('utf-16'))  # Decode the bytes to string

            if eeg_data.shape[0] > eeg_data.shape[1]:  # dimensions are weird...
                eeg_data = eeg_data.T

            return eeg_data, int(srate), channel_names

    except (OSError, KeyError):
        # If it fails to open as HDF5, fallback to standard MATLAB v7 or earlier
        loaded_file   = io.loadmat(f'{filename_prefix}.mat')
        eeg_data      = loaded_file["EEG"]["data"][0][0]
        srate         = loaded_file["EEG"]["srate"][0][0]
        chanlocs      = loaded_file["EEG"]["chanlocs"][0][0][0]['labels']
        channel_names = [chanloc[0] for chanloc in chanlocs]

        if eeg_data.shape[0] > eeg_data.shape[1]:  # dimensions are weird...
            eeg_data = eeg_data.T

        return eeg_data, int(srate), channel_names