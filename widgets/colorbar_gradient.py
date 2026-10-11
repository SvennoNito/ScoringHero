import numpy as np


def set_colorbar_gradient(cbar_img, levels):
    """Refill a colorbar ImageItem with a linear gradient between levels (keeps its size)."""
    if cbar_img is None or cbar_img.image is None:
        return
    n_x, n_y = cbar_img.image.shape  # col-major: (width, height)
    gradient = np.repeat(np.linspace(levels[0], levels[1], n_y).reshape(-1, 1), n_x, axis=1)
    cbar_img.setImage(gradient.T)
