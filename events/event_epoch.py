import numpy as np


def event_epoch(borders, epolen):
    epoch_from_to = [np.ceil(np.array(border) / epolen) for border in borders]
    epoch_array = [np.arange(start, end + 1).astype(int).tolist() for start, end in epoch_from_to]
    return epoch_array
