import os, pickle
import numpy as np
from signal_processing import *

def load_cache(ui):
    cache       = {}
    is_same_spectogram_parameters = False
    filename    = f'{ui.filename}.cache.pkl'
    if os.path.exists(filename):
        with open(filename, "rb") as file:
            cache = pickle.load(file)

        # Did spectogram parameters change?
        is_same_spectogram_parameters = (
            cache["Sampling_rate_hz"] == ui.config[0]["Sampling_rate_hz"] and 
            cache["Epoch_length_s"] == ui.config[0]["Epoch_length_s"] and
            cache["Channel_index_for_spectogram"] == ui.config[0]["Channel_index_for_spectogram"]
            )

    # Spectogram
    if "spectogram_power" not in cache or not is_same_spectogram_parameters:
        cache["spectogram_power"], cache["spectogram_freqs"], cache["spectogram_freqsOI"], cache["swa"] = spectogram_wrapper(ui)
        cache["Sampling_rate_hz"]               = ui.config[0]["Sampling_rate_hz"]
        cache["Epoch_length_s"]                 = ui.config[0]["Epoch_length_s"]
        cache["Channel_index_for_spectogram"]   = ui.config[0]["Channel_index_for_spectogram"]

    # Move cache to ui
    cache_to_ui(ui, cache)

    # Write cache
    with open(filename, "wb") as file:
        pickle.dump(cache, file)         


def cache_to_ui(ui, cache):
    ui.power, ui.freqs, ui.freqsOI, ui.swa = cache["spectogram_power"], cache["spectogram_freqs"], cache["spectogram_freqsOI"], cache["swa"]