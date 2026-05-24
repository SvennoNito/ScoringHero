"""
Validation test for the new MT-Spindle detection algorithm.
Run from the project root: uv run test_mt_spindle_new.py

Assesses:
- How many spindles are found with default parameters
- Duration distribution (should be 0.5-2.0 s)
- Spindle rate (physiologically expect ~2-8/min during N2)
- Sensitivity to the q and amin parameters
"""

import numpy as np
from pathlib import Path
from scipy.io import loadmat


def load_example_signal():
    mat_path = Path(__file__).parent / "example_data" / "example_data.mat"
    if not mat_path.exists():
        raise FileNotFoundError(f"Example data not found: {mat_path}")
    data = loadmat(str(mat_path))
    eeg = data["EEG"][0, 0]
    sfreq = float(eeg["srate"][0, 0])
    signal = np.asarray(eeg["data"], dtype=np.float64)
    if signal.ndim == 2:
        signal = signal[0]  # first channel
    return signal, sfreq


def main():
    from scoring.mt_spindle import detect_spindle

    print("=" * 60)
    print("MT-Spindle validation test")
    print("=" * 60)

    print("\nLoading example data...")
    signal, sfreq = load_example_signal()
    total_sec = len(signal) / sfreq
    print(f"  {len(signal)} samples at {sfreq:.0f} Hz = {total_sec:.1f} s ({total_sec/60:.1f} min)")
    print(f"  Amplitude: {signal.min():.1f} – {signal.max():.1f} µV  "
          f"(RMS {np.sqrt(np.mean(signal**2)):.1f} µV)")

    print("\n--- Default parameters (fmin=11, fmax=16, amin=10µV, q=95%) ---")
    spindles = detect_spindle(signal, sfreq)
    _report(spindles, total_sec)

    print("\n--- Sensitivity to q (amin=10µV fixed) ---")
    for q in [85, 90, 95, 97]:
        sp = detect_spindle(signal, sfreq, q=q)
        rate = len(sp) / total_sec * 60 if total_sec > 0 else 0
        print(f"  q={q:2d}%:  {len(sp):4d} spindles  ({rate:.1f}/min)")

    print("\n--- Sensitivity to amin (q=95% fixed) ---")
    for amin in [5.0, 10.0, 15.0, 20.0]:
        sp = detect_spindle(signal, sfreq, amin=amin)
        rate = len(sp) / total_sec * 60 if total_sec > 0 else 0
        print(f"  amin={amin:4.1f}µV:  {len(sp):4d} spindles  ({rate:.1f}/min)")

    print("\n--- Frequency bands ---")
    for fmin, fmax, label in [(11, 16, "full sigma"), (12, 15, "core sigma"), (11, 14, "slow sigma")]:
        sp = detect_spindle(signal, sfreq, fmin=fmin, fmax=fmax)
        rate = len(sp) / total_sec * 60 if total_sec > 0 else 0
        print(f"  {fmin}-{fmax} Hz ({label}):  {len(sp):4d} spindles  ({rate:.1f}/min)")

    print("\n--- First 15 spindles (default params) ---")
    spindles = detect_spindle(signal, sfreq)
    if spindles:
        for i, (s, e) in enumerate(spindles[:15], 1):
            print(f"  [{i:2d}] {s:8.2f} – {e:8.2f} s   dur={e-s:.2f}s")
    else:
        print("  (none detected)")

    print()
    print("Physiological reference:")
    print("  Healthy adult N2 sleep: ~2–8 spindles/min")
    print("  Duration: 0.5–2.0 s (most ~0.5–1.2 s)")
    print("  If recording contains non-N2 epochs, overall rate will be lower.")


def _report(spindles, total_sec):
    n = len(spindles)
    rate = n / total_sec * 60 if total_sec > 0 else 0
    print(f"  Detected: {n} spindles  ({rate:.1f}/min overall)")
    if spindles:
        durs = [e - s for s, e in spindles]
        print(f"  Duration: {min(durs):.2f}–{max(durs):.2f} s  "
              f"(mean {np.mean(durs):.2f} s, median {np.median(durs):.2f} s)")
        too_short = sum(1 for d in durs if d < 0.5)
        too_long  = sum(1 for d in durs if d >= 2.0)
        if too_short or too_long:
            print(f"  !! Out-of-range: {too_short} too short (<0.5s), {too_long} too long (>=2.0s)")


if __name__ == "__main__":
    main()
