"""
Advanced test script for spindle detection.
Tests different parameter configurations and provides detailed analysis.
"""

import numpy as np
from pathlib import Path
from scipy.signal import butter, filtfilt
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


def compute_spindle_envelope(signal, sfreq, fmin=11.0, fmax=16.0):
    """Compute envelope of filtered signal in spindle band."""
    nyq = sfreq / 2.0
    b, a = butter(4, [fmin / nyq, fmax / nyq], btype="band")
    filtered = filtfilt(b, a, signal)

    from scipy.signal import hilbert
    analytic = hilbert(filtered)
    envelope = np.abs(analytic)
    return envelope, filtered


def analyze_spindle_segment(signal, sfreq, start_idx, end_idx):
    """Analyze a detected spindle segment."""
    seg = signal[start_idx:end_idx + 1]
    envelope, filtered = compute_spindle_envelope(signal, sfreq)
    seg_envelope = envelope[start_idx:end_idx + 1]

    duration = (end_idx - start_idx) / sfreq
    rms = np.sqrt(np.mean(seg ** 2))
    envelope_rms = np.sqrt(np.mean(seg_envelope ** 2))
    peak_amplitude = np.max(np.abs(filtered[start_idx:end_idx + 1]))
    envelope_peak = np.max(seg_envelope)

    return {
        "duration_s": duration,
        "rms_uv": rms,
        "envelope_rms_uv": envelope_rms,
        "peak_amplitude_uv": peak_amplitude,
        "envelope_peak_uv": envelope_peak,
    }


def test_advanced():
    """Run advanced spindle detection tests."""
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

    # Use full available data
    signal = signal_data
    duration_min = len(signal) / sfreq

    print(f"Signal: {signal.shape[0]} samples at {sfreq} Hz = {duration_min:.1f} s")
    print()

    # Test different sensitivity levels
    configs = [
        {
            "name": "Very Conservative",
            "fmin": 12.0, "fmax": 16.0, "amin": 8.0, "dmin_s": 0.5, "dmax_s": 2.0, "q": 95.0
        },
        {
            "name": "Conservative",
            "fmin": 11.0, "fmax": 16.0, "amin": 6.0, "dmin_s": 0.5, "dmax_s": 2.0, "q": 93.0
        },
        {
            "name": "Moderate",
            "fmin": 11.0, "fmax": 16.0, "amin": 4.0, "dmin_s": 0.5, "dmax_s": 2.0, "q": 90.0
        },
        {
            "name": "Sensitive",
            "fmin": 11.0, "fmax": 16.0, "amin": 2.5, "dmin_s": 0.4, "dmax_s": 2.5, "q": 85.0
        },
        {
            "name": "Very Sensitive",
            "fmin": 10.0, "fmax": 17.0, "amin": 2.0, "dmin_s": 0.3, "dmax_s": 3.0, "q": 80.0
        },
    ]

    for config in configs:
        name = config.pop("name")
        print(f"{'='*70}")
        print(f"Configuration: {name}")
        print(f"Parameters: fmin={config['fmin']}Hz, fmax={config['fmax']}Hz, amin={config['amin']}uV, q={config['q']}%")
        print(f"{'='*70}")

        spindles = detect_spindle(signal, sfreq, **config)

        if spindles:
            print(f"Detected {len(spindles)} spindle(s):\n")
            for i, (start, end) in enumerate(spindles, 1):
                start_idx = int(start * sfreq)
                end_idx = int(end * sfreq)

                stats = analyze_spindle_segment(signal, sfreq, start_idx, end_idx)

                print(f"  Spindle {i}:")
                print(f"    Time:        {start:.2f} - {end:.2f} s")
                print(f"    Duration:    {stats['duration_s']:.3f} s")
                print(f"    RMS (raw):   {stats['rms_uv']:.2f} µV")
                print(f"    RMS (env):   {stats['envelope_rms_uv']:.2f} µV")
                print(f"    Peak (raw):  {stats['peak_amplitude_uv']:.2f} µV")
                print(f"    Peak (env):  {stats['envelope_peak_uv']:.2f} µV")
                print()
        else:
            print("No spindles detected.\n")

        print()


if __name__ == "__main__":
    test_advanced()
