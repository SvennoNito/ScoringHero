"""BDF loader: 24-bit decoding, physical scaling, record count from file size, annotation channels dropped."""

import numpy as np

from eeg.load_bdf import load_bdf


def _field(values, width):
    return "".join(str(v).ljust(width) for v in values).encode("ascii")


def _write_bdf(prefix, signals, rates, labels, dims, record_s=1, header_records=999):
    """signals: per signal int digital samples (whole records); physical range = digital range / 2."""
    n = len(signals)
    per_record = [int(r * record_s) for r in rates]
    n_records = len(signals[0]) // per_record[0]
    header = b"\xffBIOSEMI".ljust(8) + b" " * 160 + b" " * 24 + b"BDF+C".ljust(44)
    header += str(header_records).ljust(8).encode() + str(record_s).ljust(8).encode() + str(n).ljust(4).encode()
    assert len(header) == 256
    header += (_field(labels, 16) + _field([""] * n, 80) + _field(dims, 8) + _field([-100] * n, 8)
               + _field([100] * n, 8) + _field([-200] * n, 8) + _field([200] * n, 8)
               + _field([""] * n, 80) + _field(per_record, 8) + _field([""] * n, 32))
    body = bytearray()
    for r in range(n_records):
        for sig, k in zip(signals, per_record):
            for v in sig[r * k:(r + 1) * k]:
                body += int(v & 0xFFFFFF).to_bytes(3, "little")
    with open(f"{prefix}.bdf", "wb") as f:
        f.write(header + bytes(body))


def test_bdf_values_rates_and_dropped_annotations(tmp_path):
    prefix = str(tmp_path / "rec")
    fast = np.array([-200, 0, 100, 200, -1, 50, 7, 8])  # 4 Hz, 2 records
    slow = np.array([10, -10, 20, -20])                  # 2 Hz
    _write_bdf(prefix, [fast, slow, np.zeros(4, int)], [4, 2, 2],
               ["C3", "EOG", "BDF Annotations"], ["uV", "mV", ""])
    data, srate, names, units = load_bdf(prefix)
    assert names == ["C3", "EOG"] and units[0] == "uV" and srate == 4
    assert data.shape == (2, 8)
    np.testing.assert_allclose(data[0], fast / 2)  # digital +-200 -> physical +-100
