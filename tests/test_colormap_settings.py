"""Colormap choice per analysis panel: defaults, saved config, config window, drawn panels."""

import json

import numpy as np
import pyqtgraph as pg

from config.apply_changes import apply_changes
from config.default_config import default_configuration
from config.load_configuration import load_configuration
from config.open_config_window import open_config_window
from config.write_configuration import save_configuration


def _colors(colormap):
    return np.asarray(colormap.getColors())


def _items(box):
    return [box.itemText(i) for i in range(box.count())]


def test_defaults_are_the_maps_the_panels_used_before():
    general = default_configuration(2, 250, ["C3", "C4"])[0]
    assert general["Spectrogram_colormap"] == "cividis"
    assert general["Wavelet_colormap"] == "spectral"


def test_config_window_offers_current_map_viridis_magma_cividis(loaded_ui):
    open_config_window(loaded_ui)
    spectrogram = loaded_ui.SpectrogramPage.optionboxes["Spectrogram_colormap"][0]
    wavelet = loaded_ui.WaveletPage.optionboxes["Wavelet_colormap"][0]
    assert _items(spectrogram) == ["cividis", "viridis", "magma"]  # its current map is cividis
    assert _items(wavelet) == ["spectral", "viridis", "magma", "cividis"]
    loaded_ui.ConfigurationWindow.close()


def test_chosen_spectrogram_map_colors_image_and_color_bar_and_is_saved(loaded_ui):
    ui = loaded_ui
    open_config_window(ui)
    ui.SpectrogramPage.optionboxes["Spectrogram_colormap"][0].setCurrentText("magma")
    ui.ConfigurationWindow.apply_pending()

    magma = _colors(pg.colormap.get("magma"))
    assert np.array_equal(_colors(ui.SpectogramWidget.img.getColorMap()), magma)
    assert np.array_equal(_colors(ui.SpectogramWidget._cbar_img.getColorMap()), magma)
    with open(f"{ui.filename}.config.json") as f:
        assert json.load(f)[0]["Spectrogram_colormap"] == "magma"
    ui.ConfigurationWindow.close()


def test_chosen_wavelet_map_colors_image_and_color_bar(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Wavelet_colormap"] = "viridis"
    apply_changes(["Wavelet_colormap"], ui)

    viridis = _colors(pg.colormap.get("viridis"))
    assert np.array_equal(_colors(ui.TFWidget.img.getColorMap()), viridis)
    assert np.array_equal(_colors(ui.TFWidget._cbar_img.getColorMap()), viridis)


def test_saved_choice_is_restored_and_old_config_loads_with_defaults(loaded_ui):
    ui = loaded_ui
    path = f"{ui.filename}.config.json"
    names = [c["Channel_name"] for c in ui.config[1]]

    ui.config[0]["Spectrogram_colormap"] = "viridis"
    save_configuration(ui)
    restored = load_configuration(path, len(names), ui.config[0]["Sampling_rate_hz"], names)
    assert restored[0]["Spectrogram_colormap"] == "viridis"

    old = json.load(open(path))
    del old[0]["Spectrogram_colormap"], old[0]["Wavelet_colormap"]
    json.dump(old, open(path, "w"))
    loaded = load_configuration(path, len(names), ui.config[0]["Sampling_rate_hz"], names)
    assert loaded[0]["Spectrogram_colormap"] == "cividis"
    assert loaded[0]["Wavelet_colormap"] == "spectral"
