import os, pickle
import numpy as np
from signal_processing import *

def load_cache(ui):
    cache       = {}
    filename    = f'{ui.filename}.cache.pkl'
    if os.path.exists(filename):
        with open(filename, "rb") as file:
            cache = pickle.load(file)

    # Spectogram
    if "spectogram_power" not in cache:
        cache["spectogram_power"], cache["spectogram_freqs"], cache["spectogram_freqsOI"] = spectogram_wrapper(ui)


    # Move cache to ui
    cache_to_ui(ui, cache)

    # Write cache
    with open(filename, "wb") as file:
        pickle.dump(cache, file)         


def cache_to_ui(ui, cache):
    ui.power, ui.freqs, ui.freqsOI = cache["spectogram_power"], cache["spectogram_freqs"], cache["spectogram_freqsOI"]