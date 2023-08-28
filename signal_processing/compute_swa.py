import numpy as np
from scipy.signal import medfilt

def compute_swa(power, freqs):
    SWA             = np.mean(power[:, (freqs>=0.5) & (freqs<=4)], axis=1)
    SWA_smoothed    = median_filter(SWA, 5)
    # SWA = scale_swa(SWA)
    return SWA_smoothed

def scale_swa(SWA):
    SWA = (SWA - min(SWA)) / (np.percentile(SWA, 100) - min(SWA))   
    return SWA

def moving_average(SWA, window_size):
    window = np.ones(window_size) / window_size
    return np.convolve(SWA, window, mode='same')

def outlier_detection(SWA, window_size, threshold):
    SWA_smoothed    = moving_average(SWA, window_size)
    SWA_difference  = np.abs(SWA - SWA_smoothed)
    outlier_samples = np.where(SWA_difference > threshold * np.std(SWA_difference))[0]
    return outlier_samples

def median_filter(SWA, kernel_size):
    return medfilt(SWA, kernel_size)