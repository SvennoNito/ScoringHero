import os

import numpy as np

from .load_edf import to_common_rate
from .units import normalize_unit

ANNOTATION_LABELS = ("EDF Annotations", "BDF Annotations")

# Per-signal header fields: (byte offset within one signal's 256 header bytes, width).
# The file stores each field for all signals before the next field.
LABEL = (0, 16)
DIMENSION = (96, 8)
PHYSICAL_MIN, PHYSICAL_MAX, DIGITAL_MIN, DIGITAL_MAX = (104, 8), (112, 8), (120, 8), (128, 8)
SAMPLES_PER_RECORD = (216, 8)


def _fields(header, field, n_sig):
    """The header field of every signal."""
    offset, width = field
    start = offset * n_sig
    return [header[start + i * width:start + (i + 1) * width].decode("ascii", "replace").strip()
            for i in range(n_sig)]


def _decode_24bit(raw, n_records, n_samples):
    """Little-endian 24-bit two's complement samples of one signal -> int array (flat)."""
    b = raw.reshape(n_records, n_samples, 3).astype(np.int32)
    digital = b[:, :, 0] | (b[:, :, 1] << 8) | (b[:, :, 2] << 16)
    digital[digital >= 1 << 23] -= 1 << 24
    return digital.reshape(-1)


def load_bdf(filename_prefix):
    """Return (eeg_data, srate, channel_names, units) of a BioSemi 24-bit BDF file.

    Read directly (edfio decodes 16-bit EDF only). The record count is taken from the
    file size, since recorders often leave a wrong count in the header. Annotation
    channels are dropped; other signals are brought to the highest native rate.
    """
    path = f"{filename_prefix}.bdf"
    with open(path, "rb") as f:
        fixed = f.read(256)
        if fixed[0] != 0xFF or fixed[1:8] != b"BIOSEMI":
            raise ValueError("Not a BDF file (missing BIOSEMI header).")
        n_sig = int(fixed[252:256])
        record_s = float(fixed[244:252])
        header = f.read(256 * n_sig)

    labels = _fields(header, LABEL, n_sig)
    dims = _fields(header, DIMENSION, n_sig)
    pmin, pmax, dmin, dmax = (np.array(_fields(header, field, n_sig), dtype=float)
                              for field in (PHYSICAL_MIN, PHYSICAL_MAX, DIGITAL_MIN, DIGITAL_MAX))
    n_samples = np.array(_fields(header, SAMPLES_PER_RECORD, n_sig), dtype=int)

    header_bytes = 256 * (n_sig + 1)
    record_bytes = 3 * int(n_samples.sum())
    n_records = (os.path.getsize(path) - header_bytes) // record_bytes
    raw = np.memmap(path, np.uint8, "r", offset=header_bytes, shape=(n_records, record_bytes))

    keep = [i for i in range(n_sig) if labels[i] not in ANNOTATION_LABELS]
    if not keep:
        raise ValueError("The BDF file holds no signals.")
    ends = 3 * np.cumsum(n_samples)
    signals, rates, units = [], [], []
    for i in keep:
        digital = _decode_24bit(raw[:, ends[i] - 3 * n_samples[i]:ends[i]], n_records, n_samples[i])
        gain = (pmax[i] - pmin[i]) / (dmax[i] - dmin[i])
        signals.append((digital - dmin[i]) * gain + pmin[i])
        rates.append(n_samples[i] / record_s)
        units.append(normalize_unit(dims[i]))

    eeg_data, srate = to_common_rate(signals, rates, units)
    return eeg_data, srate, [labels[i] for i in keep], units
