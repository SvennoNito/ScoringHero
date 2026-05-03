"""
Test script for spindle detection using MT-Spindle approach.
Loads example data and detects spindles with different parameter configurations.
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
    else:
        print(f"Example data not found at {mat_file}")
        return None

def test_spindle_detection():
    """Test spindle detection on example data."""
    data = load_example_data()
    if data is None:
        return

    # Extract signal and sampling rate
    if 'EEG' in data:
        eeg_data = data['EEG'][0, 0]
        sfreq = float(eeg_data['srate'][0, 0])

        # Get channel data (typically first central channel like C3 or C4)
        if 'data' in eeg_data.dtype.names:
            signal_data = eeg_data['data']
        else:
            signal_data = eeg_data['data']

        # Ensure it's a numpy array and flatten if needed
        signal_data = np.asarray(signal_data, dtype=np.float64).flatten()

        # Use first 30 seconds for testing
        n_samples = int(sfreq * 30)
        signal = signal_data[:n_samples]
    else:
        print("Could not extract EEG data")
        return

    print(f"Signal shape: {signal.shape}")
    print(f"Sampling rate: {sfreq} Hz")
    print(f"Duration: {len(signal) / sfreq:.1f} s")
    print()

    # Test different parameter configurations
    configs = [
        {"name": "Conservative (high threshold)", "fmin": 11.0, "fmax": 16.0, "amin": 6.0, "dmin_s": 0.5, "dmax_s": 2.0, "q": 93.0},
        {"name": "Standard (medium threshold)", "fmin": 11.0, "fmax": 16.0, "amin": 4.0, "dmin_s": 0.5, "dmax_s": 2.0, "q": 90.0},
        {"name": "Sensitive (low threshold)", "fmin": 11.0, "fmax": 16.0, "amin": 2.5, "dmin_s": 0.4, "dmax_s": 2.5, "q": 85.0},
    ]

    all_spindles = {}
    for config in configs:
        name = config.pop("name")
        print(f"Testing: {name}")
        print(f"  Parameters: {config}")

        spindles = detect_spindle(signal, sfreq, **config)
        all_spindles[name] = spindles

        if spindles:
            print(f"  [OK] Found {len(spindles)} spindle(s)")
            for i, (start, end) in enumerate(spindles[:3]):  # Show first 3
                duration = end - start
                print(f"    Spindle {i+1}: {start:.2f}-{end:.2f} s (duration: {duration:.3f} s)")
            if len(spindles) > 3:
                print(f"    ... and {len(spindles) - 3} more")
        else:
            print(f"  [--] No spindles detected")
        print()

    # Try to visualize if matplotlib is available
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(len(all_spindles) + 1, 1, figsize=(14, 3 * (len(all_spindles) + 1)))
        if len(all_spindles) == 1:
            axes = [axes]

        # Plot raw signal
        time = np.arange(len(signal)) / sfreq
        axes[0].plot(time, signal, lw=0.5, color='black')
        axes[0].set_ylabel('Amplitude (µV)')
        axes[0].set_title('Raw EEG Signal (first 30 s)')
        axes[0].grid(alpha=0.3)

        # Plot each detection result
        for idx, (config_name, spindles) in enumerate(all_spindles.items(), 1):
            ax = axes[idx]
            ax.plot(time, signal, lw=0.5, color='lightgray')

            for start, end in spindles:
                ax.axvspan(start, end, alpha=0.3, color='green')
                ax.plot([start, end], [signal[int(start*sfreq)], signal[int(end*sfreq)]], 'g-', lw=2)

            ax.set_ylabel('Amplitude (µV)')
            ax.set_title(f'{config_name} – {len(spindles)} spindle(s) detected')
            ax.grid(alpha=0.3)
            ax.set_xlim([time[0], time[-1]])

        axes[-1].set_xlabel('Time (s)')
        plt.tight_layout()

        # Save figure
        out_path = Path(__file__).parent / "test_spindle_detection.png"
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        print(f"[OK] Visualization saved to {out_path}")

        plt.close()
    except ImportError:
        print("[--] matplotlib not available; skipping visualization")

if __name__ == "__main__":
    test_spindle_detection()
