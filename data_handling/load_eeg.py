import os, h5py
from scipy import io
from PySide6.QtWidgets import QFileDialog
from .load_config import load_configuration
from .load_scoring import load_scoring
import numpy as np
from utilities import *


def load_eeg_wrapper(ui, datatype):
    name_of_eegfile, _ = QFileDialog.getOpenFileName(
        None, "Open File", ui.default_data_path, "*.mat"
    )
    ui.filename, suffix = os.path.splitext(name_of_eegfile)
    load_eeg_config_scoring(ui, datatype)


@timing_decorator
def load_eeg_config_scoring(ui, datatype):
    if datatype == "eeglab":
        ui.eeg_data = load_eeglab(ui.filename)

    try:
        numchans = ui.eeg_data.shape[0]
    except:
        numchans = 6

    ui.config = load_configuration(f"{ui.filename}.config.json", numchans)
    ui.numepo = compute_numepo(
        ui.eeg_data.shape[1],
        ui.config[0]["Sampling_rate_hz"],
        ui.config[0]["Epoch_length_s"],
    )
    ui.stages, annotations = load_scoring(
        f"{ui.filename}.json", ui.config[0]["Epoch_length_s"], ui.numepo
    )

    id_numbers = [item['id_number'] for item in annotations]
    for id_number in set(id_numbers):
        container_index = np.where(np.array(id_numbers) == id_number)[0].tolist()
        for container in np.array(annotations)[container_index]:
            ui.AnnotationContainer[id_number].label = container['id']
            ui.AnnotationContainer[id_number].borders.append([container['start'], container['end']])
            ui.AnnotationContainer[id_number].epochs.append(container['epoch'])



def load_eeglab(filename_prefix):
    if io.matlab.miobase.get_matfile_version(filename_prefix)[0] == 2:  # v7.3 files
        with h5py.File(filename_prefix, "r") as eeg_file:
            eeg_data = eeg_file["EEG"]["eeg_data"][:]
            if eeg_data.shape[0] > eeg_data.shape[1]:  # dimensions are weird ....
                eeg_data = eeg_data.T
    else:
        eeg_data = io.loadmat(filename_prefix)["EEG"]["data"][0][0]
    return eeg_data


def compute_numepo(npoints, srate, epolen):
    return np.floor(npoints / srate / epolen).astype(int)
