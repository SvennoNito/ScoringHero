import numpy as np


def trim_power(power, freqs, upper_limit, lower_limit):
    power = power[np.where((freqs <= upper_limit) & (freqs >= lower_limit))]
    freqs = freqs[np.where((freqs <= upper_limit) & (freqs >= lower_limit))]
    return power, freqs
