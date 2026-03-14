import numpy as np


def trim_power(power, freqs, lower_limit, upper_limit):
    mask = (freqs >= lower_limit) & (freqs <= upper_limit)
    return power[mask], freqs[mask]
