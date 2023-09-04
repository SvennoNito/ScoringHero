import os, pickle
import numpy as np
from signal_processing.compute_spectogram import spectogram_wrapper


def load_cache(ui):
    cache = {}
    is_same_spectogram_parameters = False
    filename = f"{ui.filename}.cache.pkl"
    if os.path.exists(filename):
        with open(filename, "rb") as file:
            cache = pickle.load(file)

        # Did spectogram parameters change?
        is_same_spectogram_parameters = (
            cache["Sampling_rate_hz"] == ui.config[0]["Sampling_rate_hz"]
            and cache["Epoch_length_s"] == ui.config[0]["Epoch_length_s"]
            and cache["Channel_for_spectogram"] == ui.config[0]["Channel_for_spectogram"]
            and "spectogram" in cache
        )

    # Spectogram
    if not is_same_spectogram_parameters:
        ui.power, ui.freqs, ui.freqsOI, ui.swa = spectogram_wrapper(ui)
        cache = ui_to_cache(ui, cache)
    else:
        ui.power, ui.freqs, ui.freqsOI, ui.swa = cache["spectogram"].values()

    # Write cache
    write_cache(ui, cache)


def write_cache(ui, cache):
    with open(f"{ui.filename}.cache.pkl", "wb") as file:
        pickle.dump(cache, file)    



def ui_to_cache(ui, cache={}):
    cache["spectogram"] = {}
    cache["spectogram"]["power"] = ui.power
    cache["spectogram"]["freqs"] = ui.freqs
    cache["spectogram"]["freqsOI"] = ui.freqsOI
    cache["spectogram"]["swa"] = ui.swa

    cache["Sampling_rate_hz"] = ui.config[0]["Sampling_rate_hz"]
    cache["Epoch_length_s"] = ui.config[0]["Epoch_length_s"]
    cache["Channel_for_spectogram"] = ui.config[0]["Channel_for_spectogram"]
    return cache