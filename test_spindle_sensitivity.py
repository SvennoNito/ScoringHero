"""
Test spindle detection at different sensitivity levels.
"""

import numpy as np
from pathlib import Path
from scoring.mt_spindle import detect_spindle


def load_example_data():
    example_dir = Path(__file__).parent / "example_data"
    mat_file = example_dir / "example_data.mat"
    if mat_file.exists():
        from scipy.io import loadmat
        return loadmat(str(mat_file))
    return None


def test_sensitivity():
    data = load_example_data()
    if data is None:
        return

    eeg_data = data['EEG'][0, 0]
    sfreq = float(eeg_data['srate'][0, 0])
    signal_data = np.asarray(eeg_data['data'], dtype=np.float64).flatten()

    # Use 2 minutes for testing
    n_samples = int(sfreq * 120)
    signal = signal_data[:n_samples]

    print(f"Testing on {len(signal) / sfreq:.0f} seconds of data")
    print()

    configs = [
        {"name": "Conservative", "amin_db": 4.0, "q": 90.0},
        {"name": "Moderate", "amin_db": 3.0, "q": 85.0},
        {"name": "Sensitive", "amin_db": 2.0, "q": 80.0},
        {"name": "Very Sensitive", "amin_db": 1.5, "q": 75.0},
    ]

    for cfg in configs:
        name = cfg["name"]
        spindles = detect_spindle(
            signal, sfreq,
            fmin=11.0, fmax=16.0,
            amin_db=cfg["amin_db"],
            dmin_s=0.5, dmax_s=2.0,
            q=cfg["q"]
        )
        print(f"{name:15s} (amin_db={cfg['amin_db']:.1f}dB, q={cfg['q']:.0f}%): {len(spindles):2d} spindles")


if __name__ == "__main__":
    test_sensitivity()
