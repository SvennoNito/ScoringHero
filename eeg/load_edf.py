import numpy as np
from edfio import read_edf as _read_edf
from .resample import resample_to_rate
from .units import TO_UV, normalize_unit


def to_common_rate(raw_signals, rates, units, scale_to_uv=False):
    """Bring signals to the highest native rate, zero-pad to equal length, optionally
    convert voltage units to uV (units is updated in place). Returns (eeg_data, srate)."""
    srate = int(round(max(rates)))
    signals = []
    for i, (data, rate) in enumerate(zip(raw_signals, rates)):
        data = resample_to_rate(np.asarray(data, dtype=float), rate, srate)
        if scale_to_uv and units[i] in TO_UV:
            data = data * TO_UV[units[i]]
            units[i] = 'uV'
        signals.append(data)

    max_len = max(len(s) for s in signals)
    eeg_data = np.array([
        np.pad(s, (0, max_len - len(s))) if len(s) < max_len else s
        for s in signals
    ])
    return eeg_data, srate


def load_edf(filename_prefix, scale_to_uv=False):
    """Return (eeg_data, srate, channel_names, units).

    All signals are returned at the highest native sampling rate (lower-rate signals
    are upsampled). With scale_to_uv, signals with a voltage unit (V, mV, uV) are
    converted to uV; other units are left untouched.
    """
    edf = _read_edf(f'{filename_prefix}.edf')
    channel_names = [s.label for s in edf.signals]
    units = [normalize_unit(s.physical_dimension) for s in edf.signals]
    rates = [s.sampling_frequency for s in edf.signals]
    eeg_data, srate = to_common_rate([s.data for s in edf.signals], rates, units, scale_to_uv)
    return eeg_data, srate, channel_names, units
