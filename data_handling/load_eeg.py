
import os, h5py
from scipy import io
from PySide6.QtWidgets import QFileDialog
from .load_config import load_configuration 
from .load_scoring import load_scoring
import numpy as np


def load_eeg_wrapper(default_data_path, **kwargs):
    name_of_eegfile, _              = QFileDialog.getOpenFileName(None, 'Open File', default_data_path, '*.mat;*json')
    name_of_eegfile_prefix, suffix  = os.path.splitext(name_of_eegfile)
    return load_all_important(name_of_eegfile_prefix, kwargs)
                         

def load_all_important(name_of_eegfile_prefix, kwargs):

    if kwargs['datatype'] == 'eeglab':
        eeg_data = load_mat_eeglab(name_of_eegfile_prefix)

    config_settings = load_configuration(f'{name_of_eegfile_prefix}.config.json', eeg_data.shape[0])
    num_epo         = compute_numepo(eeg_data.shape[1], config_settings[0]['Sampling_rate_hz'], config_settings[0]['Epoch_length_s'])
    scoring_data, annotations = load_scoring(f'{name_of_eegfile_prefix}.json', config_settings[0]['Epoch_length_s'], num_epo)
    return eeg_data, config_settings, scoring_data, annotations, name_of_eegfile_prefix          

def compute_numepo(npoints, srate, epolen):
    return np.floor(npoints/srate/epolen).astype(int)

    # Integrate EEG data into structure
    #mainwindow.EEG.data = eeg_data

    # Load and apply configuration settings
    #configuration_settings = load_configuration_file(name_of_eegfile_prefix + '.config.json', number_of_channels)
    #apply_configuration_settings(mainwindow, configuration_settings)

def load_mat_eeglab(name_of_eegfile_prefix):
    if io.matlab.miobase.get_matfile_version(name_of_eegfile_prefix)[0] == 2: #v7.3 files
        with h5py.File(name_of_eegfile_prefix, "r") as eeg_file:
            eeg_data = eeg_file['EEG']['eeg_data'][:]
            if eeg_data.shape[0] > eeg_data.shape[1]: # dimensions are weird ....
                eeg_data = eeg_data.T
    else:
        eeg_data = io.loadmat(name_of_eegfile_prefix)['EEG']['data'][0][0]    
    return eeg_data