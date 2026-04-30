"""
Debug script for YASA spindle detection.
Loads the same example data as ScoringHero devmode and tests YASA directly.
"""

import os
import sys
import numpy as np
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load EEG the same way ScoringHero does
from eeg.load_eeglab import load_eeglab

# Load the example data file (load_eeglab expects path WITHOUT .mat extension)
data_path = Path(__file__).parent / "example_data" / "example_data"
print(f"Loading EEG data from: {data_path}.mat")

eeg_data, srate, channel_names = load_eeglab(str(data_path))
print(f"  Shape: {eeg_data.shape}")
print(f"  Sampling rate: {srate} Hz")
print(f"  Channels: {channel_names}")
print(f"  Data dtype: {eeg_data.dtype}")
print(f"  Data range: [{eeg_data.min():.2f}, {eeg_data.max():.2f}] µV")

# Try importing YASA
try:
    import yasa
    print(f"\nYASA imported successfully (version: {yasa.__version__})")
except ImportError as e:
    print(f"\nERROR: YASA not installed!")
    print(f"Install with: uv pip install yasa")
    sys.exit(1)

# Test on first channel (usually the best EEG channel)
ch_idx = 0
signal_1d = eeg_data[ch_idx].copy().astype(np.float64)
print(f"\n=== Testing spindle detection on channel: {channel_names[ch_idx]} ===")
print(f"Signal shape: {signal_1d.shape}")
print(f"Signal range: [{signal_1d.min():.2f}, {signal_1d.max():.2f}] µV")

# Try with default YASA parameters first
print("\n--- Attempt 1: Default YASA parameters ---")
try:
    spindles = yasa.spindles_detect(
        signal_1d,
        srate,
        ch_names=[channel_names[ch_idx]],
    )
    print(f"Result type: {type(spindles)}")
    print(f"Result dir: {[x for x in dir(spindles) if not x.startswith('_')]}")

    # Try accessing as DataFrame
    if hasattr(spindles, 'summary'):
        summary = spindles.summary()
        print(f"Summary:\n{summary}")
        if summary is not None and len(summary) > 0:
            print(f"Number of spindles found: {len(summary)}")
        else:
            print("Summary is empty")

    # Try accessing underlying data
    if hasattr(spindles, 'values'):
        print(f"spindles.values: {spindles.values}")
    if hasattr(spindles, 'data'):
        print(f"spindles.data: {spindles.data}")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Try with loosened thresholds
print("\n--- Attempt 2: Loosened thresholds ---")
try:
    spindles = yasa.spindles_detect(
        signal_1d,
        srate,
        ch_names=[channel_names[ch_idx]],
        thresh={
            "rel_pow": 0.1,
            "corr": 0.5,
            "rms": 1.0,
        },
    )
    print(f"Result type: {type(spindles)}")
    if spindles is not None:
        count = 0
        try:
            for sp in spindles:
                count += 1
            print(f"Number of spindles found: {count}")
        except:
            print("Could not iterate")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# Try with very loose thresholds
print("\n--- Attempt 3: Very loose thresholds ---")
try:
    spindles = yasa.spindles_detect(
        signal_1d,
        srate,
        ch_names=[channel_names[ch_idx]],
        thresh={
            "rel_pow": 0.05,
            "corr": 0.3,
            "rms": 0.5,
        },
    )
    print(f"Result type: {type(spindles)}")
    if spindles is not None:
        count = 0
        try:
            for sp in spindles:
                count += 1
            print(f"Number of spindles found: {count}")
        except:
            print("Could not iterate")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# Try without thresholds (using individual threshold None values)
print("\n--- Attempt 4: Disable correlation and RMS thresholds ---")
try:
    spindles = yasa.spindles_detect(
        signal_1d,
        srate,
        ch_names=[channel_names[ch_idx]],
        thresh={
            "rel_pow": 0.1,
            "corr": None,  # Disable
            "rms": None,   # Disable
        },
    )
    print(f"Result type: {type(spindles)}")
    if spindles is not None:
        count = 0
        try:
            for sp in spindles:
                count += 1
            print(f"Number of spindles found: {count}")
        except:
            print("Could not iterate")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print("\n=== Debug complete ===")
