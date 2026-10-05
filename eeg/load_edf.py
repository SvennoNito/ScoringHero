import numpy as np
from edfio import read_edf as _read_edf
from .resample import resample_to_rate

# physical dimension -> factor to microvolts (only voltage units are converted)
_TO_UV = {'V': 1e6, 'mV': 1e3, 'uV': 1.0}


def _normalize_unit(dimension):
    """'µV'/'μV' -> 'uV'; empty dimension -> None (unknown)."""
    unit = dimension.strip().replace('\u00b5', 'u').replace('\u03bc', 'u')
    return unit or None


def load_edf(filename_prefix, scale_to_uv=False):
    """Return (eeg_data, srate, channel_names, units).

    All signals are returned at the highest native sampling rate (lower-rate signals
    are upsampled). With scale_to_uv, signals with a voltage unit (V, mV, uV) are
    converted to uV; other units are left untouched.
    """
    edf = _read_edf(f'{filename_prefix}.edf')
    channel_names = [s.label for s in edf.signals]
    units = [_normalize_unit(s.physical_dimension) for s in edf.signals]
    rates = [s.sampling_frequency for s in edf.signals]
    srate = int(round(max(rates)))

    signals = []
    for s, rate, i in zip(edf.signals, rates, range(len(rates))):
        data = resample_to_rate(np.asarray(s.data, dtype=float), rate, srate)
        if scale_to_uv and units[i] in _TO_UV:
            data = data * _TO_UV[units[i]]
            units[i] = 'uV'
        signals.append(data)

    max_len = max(len(s) for s in signals)
    eeg_data = np.array([
        np.pad(s, (0, max_len - len(s))) if len(s) < max_len else s
        for s in signals
    ])
    return eeg_data, srate, channel_names, units
