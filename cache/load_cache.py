import os, pickle
from signal_processing.spectogram_to_ui import spectogram_to_ui
from .write_cache import write_cache
from .ui_to_cache import ui_to_cache


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
            and cache["Channel_for_spectogram"]
            == ui.config[0]["Channel_for_spectogram"]
            and "spectogram" in cache
        )

    # Spectogram
    if not is_same_spectogram_parameters:
        ui.power, ui.freqs, ui.freqsOI, ui.swa = spectogram_to_ui(ui)
        cache = ui_to_cache(ui, cache)
    else:
        ui.power, ui.freqs, ui.freqsOI, ui.swa = cache["spectogram"].values()

    # Write cache
    write_cache(ui, cache)
