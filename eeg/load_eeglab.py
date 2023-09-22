import h5py
from scipy import io


def load_eeglab(filename_prefix):
    if io.matlab.miobase.get_matfile_version(filename_prefix)[0] == 2:  # v7.3 files
        with h5py.File(filename_prefix, "r") as eeg_file:
            eeg_data = eeg_file["EEG"]["eeg_data"][:]
            srate    = eeg_file["EEG"]["srate"][:]
            if eeg_data.shape[0] > eeg_data.shape[1]:  # dimensions are weird ....
                eeg_data = eeg_data.T
    else:
        eeg_data = io.loadmat(filename_prefix)["EEG"]["data"][0][0]
        srate    = io.loadmat(filename_prefix)["EEG"]["srate"][0][0][0][0]
    return eeg_data, srate
