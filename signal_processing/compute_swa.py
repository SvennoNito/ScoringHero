import numpy as np


def compute_swa(power, freqs):
    SWA = np.mean(power[:, (freqs >= 0.5) & (freqs <= 4)], axis=1)
    return SWA
