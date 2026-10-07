"""
seed_runner.py  —  executed by ScoringHero as a subprocess inside the SEED
conda environment (Python 3.7 + TensorFlow 1.x).

Called by ScoringHero like:
    python seed_runner.py \
        --seed_dir  C:/path/to/Sleep-EEG-Event-Detector \
        --input     /tmp/signal.npy \
        --sfreq     256 \
        --event_type  kc \
        --output    /tmp/events.json

Writes a JSON file: [[start_sec, end_sec], ...]
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.signal import resample as scipy_resample

# ---------------------------------------------------------------------------
# TF1 compatibility shim — must run before any sleeprnn import.
# SEED was written for TF1; TF2 ships a full compat.v1 layer that replicates
# all TF1 session-based APIs. We expose it as the top-level 'tensorflow'
# module so every `import tensorflow as tf` inside sleeprnn gets TF1 behaviour.
# ---------------------------------------------------------------------------
def _apply_tf1_compat():
    import tensorflow.compat.v1 as _tf1
    _tf1.disable_v2_behavior()
    import sys
    sys.modules["tensorflow"] = _tf1

_apply_tf1_compat()
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed_dir",    required=True)
    parser.add_argument("--input",       required=True)
    parser.add_argument("--sfreq",       required=True, type=float)
    parser.add_argument("--event_type",  required=True, choices=["kc", "spindle"])
    parser.add_argument("--output",      required=True)
    args = parser.parse_args()

    if args.seed_dir not in sys.path:
        sys.path.insert(0, args.seed_dir)

    signal_1d = np.load(args.input).astype(np.float32)
    events = detect(signal_1d, args.sfreq, args.event_type, args.seed_dir)

    with open(args.output, "w") as f:
        json.dump(events, f)


def detect(signal_1d, sfreq, event_type, seed_dir):
    from sleeprnn.nn.models import WaveletBLSTM
    from sleeprnn.common import pkeys
    from sleeprnn.detection import postprocessor as seed_pp

    # SEED models run at 200 Hz
    SEED_SFREQ = 200.0
    if abs(sfreq - SEED_SFREQ) > 0.5:
        n_out = int(round(len(signal_1d) * SEED_SFREQ / sfreq))
        signal_1d = scipy_resample(signal_1d, n_out).astype(np.float32)

    subdir = "kc" if event_type == "kc" else "ss"
    ckpt_dir = _find_ckpt(seed_dir, subdir)

    params = pkeys.default_params.copy()
    model = WaveletBLSTM(params=params, logdir=ckpt_dir)
    model.load_checkpoint(ckpt_dir)

    proba = model.predict_proba_from_vector(signal_1d)

    threshold = params.get(pkeys.PREDICTION_THRESHOLD, 0.5)
    binary = (proba >= threshold).astype(np.int32)
    stamps = seed_pp.seq2stamp(binary)

    if stamps is None or len(stamps) == 0:
        return []

    return [[float(s[0]) / SEED_SFREQ, float(s[1]) / SEED_SFREQ] for s in stamps]


def _find_ckpt(seed_dir, subdir):
    candidate = os.path.join(seed_dir, "ckpt", subdir)
    if os.path.isdir(candidate):
        return candidate

    ckpt_root = os.path.join(seed_dir, "ckpt")
    if os.path.isdir(ckpt_root):
        for name in os.listdir(ckpt_root):
            if subdir in name.lower() and os.path.isdir(os.path.join(ckpt_root, name)):
                return os.path.join(ckpt_root, name)

    raise FileNotFoundError(
        f"No SEED checkpoint found for '{subdir}' in {ckpt_root}.\n"
        "Expected a subdirectory whose name contains 'kc' or 'ss'."
    )


if __name__ == "__main__":
    main()
