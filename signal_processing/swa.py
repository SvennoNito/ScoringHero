import numpy as np

def compute_swa(power, freqs):
    SWA = np.mean(power[:, (freqs>=0.5) & (freqs<=4)], axis=1)
    SWA = scale_swa(SWA)
    return SWA

def scale_swa(SWA):
    SWA = (SWA - min(SWA)) / (np.percentile(SWA, 99) - min(SWA))   
    return SWA