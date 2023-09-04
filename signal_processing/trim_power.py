import numpy as np


def trim_power(power, freqs, lower_limit, upper_limit):
    power = power[np.where((freqs <= upper_limit) & (freqs >= lower_limit))]
    freqs = freqs[np.where((freqs <= upper_limit) & (freqs >= lower_limit))]
    return power, freqs
