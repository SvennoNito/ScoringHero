"""The recording's disk cache file ({filename}.cache.pkl)."""

import os
import pickle


def read_cache(ui):
    """Contents of the recording's disk cache file; {} if there is none."""
    filename = f"{ui.filename}.cache.pkl"
    if not os.path.exists(filename):
        return {}
    with open(filename, "rb") as file:
        return pickle.load(file)


def write_cache(ui, cache):
    with open(f"{ui.filename}.cache.pkl", "wb") as file:
        pickle.dump(cache, file)
