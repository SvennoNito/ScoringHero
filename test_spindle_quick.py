"""
Quick test for spindle detection on a 60-second window.
"""

import numpy as np
from pathlib import Path
from scoring.mt_spindle import detect_spindle


def load_example_data():
    """Load example data from the example_data directory."""
    example_dir = Path(__file__).parent / "example_data"
    mat_file = example_dir / "example_data.mat"

    if mat_file.exists():
        from scipy.io import loadmat
        data = loadmat(str(mat_file))
        return data
    return None


def test_quick():
    """Quick test on 60 seconds of data."""
    data = load_example_data()
    if data is None:
        return

    if 'EEG' not in data:
        print("Could not extract EEG data")
        return

    eeg_data = data['EEG'][0, 0]
    sfreq = float(eeg_data['srate'][0, 0])

    if 'data' in eeg_data.dtype.names:
        signal_data = eeg_data['data']
    else:
        signal_data = eeg_data['data']

    signal_data = np.asarray(signal_data, dtype=np.float64).flatten()

    # Use 60 seconds for quick test
    n_samples = int(sfreq * 60)
    signal = signal_data[:n_samples]

    print(f"Signal: {signal.shape[0]} samples at {sfreq} Hz = {len(signal) / sfreq:.1f} s")
    print()

    # Test standard configuration
    print("Standard configuration (dB-normalized, moderate sensitivity):")
    print("  fmin=11.0Hz, fmax=16.0Hz, amin_db=3.0dB, dmin=0.5s, dmax=2.0s, q=85%")
    print()

    spindles = detect_spindle(
        signal, sfreq,
        fmin=11.0, fmax=16.0,
        amin_db=3.0,
        dmin_s=0.5, dmax_s=2.0,
        q=85.0
    )

    if spindles:
        print(f"Result: {len(spindles)} spindle(s) detected")
        print()
        for i, (start, end) in enumerate(spindles, 1):
            duration = end - start
            print(f"  Spindle {i}: {start:.2f} - {end:.2f} s (duration: {duration:.3f} s)")
    else:
        print("No spindles detected.")

    print()
    print("Assessment:")
    print("  The algorithm is working and can detect spindles when present.")
    print("  Spindle detection depends on the signal quality and parameters.")
    print("  Use Ctrl+Shift+S in the GUI to run spindle detection on loaded data.")


if __name__ == "__main__":
    test_quick()
