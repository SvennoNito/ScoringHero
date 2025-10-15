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

            if eeg_data.shape[0] > eeg_data.shape[1]:  # dimensions are weird...
                eeg_data = eeg_data.T
            nbchans = eeg_data.shape[0]

            try:  # Try to load chanlocs, handle exceptions
                chanlocs = np.array(loaded_file["EEG"]["chanlocs"]['labels']).flatten()
                if len(chanlocs) != nbchans:
                    raise ValueError(f"Number of channels in chanlocs ({len(chanlocs)}) does not match EEG.data ({nbchans}).") #Raise ValueError to use except block
                channel_names = []
                for chanloc in chanlocs:
                    referred_data = loaded_file[chanloc][()]
                    channel_names.append(referred_data.tobytes().decode('utf-16'))
            
            except (KeyError, ValueError) as e:  
                channel_names = [f"CH{i+1}" for i in range(nbchans)]
                print(f"*** Warning: {e}")
                print(f"*** Using default channel names instead.")

            return eeg_data, int(srate), channel_names

    except (OSError, KeyError):
        # If it fails to open as HDF5, fallback to standard MATLAB v7 or earlier
        loaded_file   = io.loadmat(f'{filename_prefix}.mat')
        eeg_data      = loaded_file["EEG"]["data"][0][0]
        srate         = loaded_file["EEG"]["srate"][0][0]

        if eeg_data.shape[0] > eeg_data.shape[1]:  # dimensions are weird...
            eeg_data = eeg_data.T
        nbchans = eeg_data.shape[0]

        try:
            chanlocs    = loaded_file["EEG"]["chanlocs"][0][0][0]['labels']
            chanlocs2   = loaded_file["EEG"]["chanlocs"][0][0]['labels'] # Matlab 2025b saves the data differently somehow
            if len(chanlocs) == nbchans:  # Check channel count
                channel_names = [chanloc[0] for chanloc in chanlocs]
            else:
                if len(chanlocs2) == nbchans: 
                    channel_names = [chanloc[0][0] for chanloc in chanlocs2]
                else:
                    raise ValueError(f"Number of channels in chanlocs ({len(chanlocs)}) does not match EEG.data ({nbchans}).") #Raise ValueError to use except block
        except (KeyError, IndexError, ValueError) as e: #chanlocs might be missing or wrongly sized
            channel_names = [f"CH{i+1}" for i in range(nbchans)]
            print(f"*** Warning: {e}")
            print(f"*** Using default channel names instead.")

        return eeg_data, int(srate), channel_names