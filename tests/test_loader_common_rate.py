"""
Tests for the recording loader: common sampling rate (highest native rate),
polyphase upsampling of lower-rate signals, per-signal units and per-signal
"EDF in volts" conversion. Uses example_data/Sven_Night01.edf (skips if missing).
"""

import os
import numpy as np

EDF_PREFIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example_data", "Sven_Night01")


def _example_available():
    if not os.path.exists(EDF_PREFIX + ".edf"):
        print("[SKIP] example_data/Sven_Night01.edf not found")
        return False
    return True


def _is_acc(name):
    return "acc_" in name.lower()


def test_resample_to_rate_synthetic():
    """Upsampling keeps duration and shape of a slow sinusoid (no zero padding)."""
    from eeg.resample import resample_to_rate
    t = np.arange(0, 600) / 50.0
    x = np.vstack([np.sin(2 * np.pi * 0.1 * t) + 1.0, np.cos(2 * np.pi * 0.2 * t)])
    y = resample_to_rate(x, 50, 256)
    assert y.shape == (2, 3072)
    t_new = np.arange(y.shape[1]) / 256.0
    expected = np.sin(2 * np.pi * 0.1 * t_new) + 1.0
    mid = slice(1000, -1000)
    assert np.max(np.abs(y[0, mid] - expected[mid])) < 0.01
    assert resample_to_rate(x, 50, 50) is x
    print("[OK] resample_to_rate synthetic")


def test_all_signals_equal_length_at_highest_rate():
    if not _example_available():
        return
    from edfio import read_edf
    from eeg.load_edf import load_edf
    edf = read_edf(EDF_PREFIX + ".edf")
    max_rate = max(s.sampling_frequency for s in edf.signals)
    duration = max(len(s.data) / s.sampling_frequency for s in edf.signals)

    eeg_data, srate, names, units = load_edf(EDF_PREFIX)
    assert srate == int(round(max_rate))
    assert eeg_data.ndim == 2 and eeg_data.shape[0] == len(names) == len(units) == len(edf.signals)
    assert abs(eeg_data.shape[1] / srate - duration) < 1.0 / srate
    print(f"[OK] {eeg_data.shape[0]} signals, equal length {eeg_data.shape[1]} at {srate} Hz")


def test_accelerometer_nonconstant_in_last_part_of_night():
    if not _example_available():
        return
    from eeg.load_edf import load_edf
    eeg_data, srate, names, units = load_edf(EDF_PREFIX)
    acc_idx = [i for i, n in enumerate(names) if _is_acc(n)]
    assert acc_idx, f"no accelerometer channels in {names}"
    n = eeg_data.shape[1]
    for i in acc_idx:
        last = eeg_data[i, int(n * 0.8):]
        assert np.std(last) > 0, f"{names[i]} is constant in the last 20% of the night"
    print("[OK] accelerometer signals non-constant in last 20%")


def test_edf_in_volts_converts_only_voltage_signals():
    if not _example_available():
        return
    from eeg.load_edf import load_edf
    raw, srate, names, raw_units = load_edf(EDF_PREFIX)
    conv, srate_c, names_c, units = load_edf(EDF_PREFIX, scale_to_uv=True)
    assert srate_c == srate and names_c == names and conv.shape == raw.shape

    factor = {"V": 1e6, "mV": 1e3, "uV": 1.0}
    checked_acc = checked_eeg = False
    for i, name in enumerate(names):
        if raw_units[i] in factor:
            assert units[i] == "uV"
            assert np.allclose(conv[i], raw[i] * factor[raw_units[i]])
            checked_eeg = True
        else:
            assert units[i] == raw_units[i]
            assert np.array_equal(conv[i], raw[i]), f"{name} ({raw_units[i]}) must stay untouched"
            checked_acc = checked_acc or _is_acc(name)
    assert checked_eeg, f"no voltage signals found, units: {raw_units}"
    assert checked_acc, f"no non-voltage accelerometer found, units: {raw_units}"
    for i, name in enumerate(names):
        if _is_acc(name):
            assert units[i].lower() == "g", f"{name} unit is {units[i]!r}"
    print("[OK] EDF in volts: voltage signals -> uV, accelerometer stays in g")


if __name__ == "__main__":
    test_resample_to_rate_synthetic()
    test_all_signals_equal_length_at_highest_rate()
    test_accelerometer_nonconstant_in_last_part_of_night()
    test_edf_in_volts_converts_only_voltage_signals()
