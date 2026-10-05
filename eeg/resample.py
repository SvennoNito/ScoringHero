from fractions import Fraction
import numpy as np
from scipy.signal import resample_poly


def resample_to_rate(data, srate, target_srate):
    """Polyphase-resample data (last axis = time) from srate to target_srate.

    Output length is round(n * target_srate / srate). Returns data unchanged if the
    rates are equal.
    """
    if srate == target_srate:
        return data
    ratio = Fraction(target_srate).limit_denominator(1000) / Fraction(srate).limit_denominator(1000)
    n_target = int(round(data.shape[-1] * target_srate / srate))
    # 'line' padding avoids edge transients on signals with a constant offset (e.g. gravity in acc)
    out = resample_poly(data, ratio.numerator, ratio.denominator, axis=-1, padtype='line')
    if out.shape[-1] > n_target:
        return out[..., :n_target]
    if out.shape[-1] < n_target:
        pad = [(0, 0)] * (out.ndim - 1) + [(0, n_target - out.shape[-1])]
        return np.pad(out, pad, mode='edge')
    return out
