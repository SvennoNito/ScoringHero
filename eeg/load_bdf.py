import numpy as np

from .load_edf import to_common_rate
from .units import normalize_unit

ANNOTATION_LABELS = ("EDF Annotations", "BDF Annotations")


def _fields(header, offset_per_signal, n_sig, width):
    """The header field of every signal; offset_per_signal is the field's byte offset
    within one signal's 256 header bytes (fields are stored signal after signal)."""
    start = offset_per_signal * n_sig
    return [header[start + i * width:start + (i + 1) * width].decode("ascii", "replace").strip()
            for i in range(n_sig)]


def load_bdf(filename_prefix):
    """Return (eeg_data, srate, channel_names, units) of a BioSemi 24-bit BDF file.

    Read directly (edfio decodes 16-bit EDF only). The record count is taken from the
    file size, since recorders often leave a wrong count in the header. Annotation
    channels are dropped; other signals are brought to the highest native rate.
    """
    with open(f"{filename_prefix}.bdf", "rb") as f:
        fixed = f.read(256)
        if fixed[0] != 0xFF or fixed[1:8] != b"BIOSEMI":
            raise ValueError("Not a BDF file (missing BIOSEMI header).")
        n_sig = int(fixed[252:256])
        record_s = float(fixed[244:252])
        header = f.read(256 * n_sig)

    labels = _fields(header, 0, n_sig, 16)
    dims = _fields(header, 96, n_sig, 8)
    pmin, pmax, dmin, dmax = (np.array(_fields(header, o, n_sig, 8), dtype=float)
                              for o in (104, 112, 120, 128))
    n_samples = np.array(_fields(header, 216, n_sig, 8), dtype=int)

    record_bytes = 3 * int(n_samples.sum())
    n_records = (len(np.memmap(f"{filename_prefix}.bdf", np.uint8, "r")) - 256 * (n_sig + 1)) // record_bytes
    raw = np.memmap(f"{filename_prefix}.bdf", np.uint8, "r", offset=256 * (n_sig + 1),
                    shape=(n_records, record_bytes))

    keep = [i for i in range(n_sig) if labels[i] not in ANNOTATION_LABELS]
    if not keep:
        raise ValueError("The BDF file holds no signals.")
    ends = 3 * np.cumsum(n_samples)
    signals, rates, units = [], [], []
    for i in keep:
        b = raw[:, ends[i] - 3 * n_samples[i]:ends[i]].reshape(n_records, n_samples[i], 3).astype(np.int32)
        digital = b[:, :, 0] | (b[:, :, 1] << 8) | (b[:, :, 2] << 16)
        digital[digital >= 1 << 23] -= 1 << 24  # 24-bit two's complement
        gain = (pmax[i] - pmin[i]) / (dmax[i] - dmin[i])
        signals.append((digital.reshape(-1) - dmin[i]) * gain + pmin[i])
        rates.append(n_samples[i] / record_s)
        units.append(normalize_unit(dims[i]))

    eeg_data, srate = to_common_rate(signals, rates, units)
    return eeg_data, srate, [labels[i] for i in keep], units
