import numpy as np

def number_of_epochs(npoints, srate, epolen):
    return np.floor(npoints / srate / epolen).astype(int)
