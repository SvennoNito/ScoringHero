"""Colormaps the spectrogram and time-frequency panels can use. The first entry of each
list is the panel's original map and its default."""

import os

import numpy as np

SPECTROGRAM_COLORMAPS = ("cividis", "viridis", "magma")
WAVELET_COLORMAPS = ("spectral", "viridis", "magma", "cividis")


def get_colormap(name, app_path):
    """pyqtgraph ColorMap for `name`; "spectral" is read from spectral.txt in app_path
    (RGB floats 0-1, one row per stop; bundled with the app)."""
    import pyqtgraph as pg

    if name != "spectral":
        return pg.colormap.get(name)
    rgb = np.loadtxt(os.path.join(app_path, "spectral.txt"))
    rgba = np.hstack([
        (rgb * 255).clip(0, 255).astype(np.uint8),
        np.full((len(rgb), 1), 255, dtype=np.uint8),
    ])
    return pg.ColorMap(np.linspace(0.0, 1.0, len(rgb)), rgba)
