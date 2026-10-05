"""
ezscore_worker.py — executed by ScoringHero as a subprocess inside the ezscore
environment (Python 3.9-3.11 + TensorFlow 2.15).

Called by ScoringHero like:

    python ezscore_worker.py --job C:/tmp/job.json

The job file is JSON:

    {
      "data_npy":    "<path>",   # float64 (2, n_samples) array, VOLTS
      "sfreq":       250.0,      # sampling rate of that array
      "model_dir":   "<path>",   # TensorFlow SavedModel directory
      "normalize":   true,       # median/IQR normalization (ez6 / ez6moe)
      "out_npz":     "<path>",   # where the results are written
      "summary_png": "<path>",   # optional; null to skip the summary figure
      "title":       "ez6"
    }

The result .npz contains:

    hypnogram : int64 (n_epochs,)  1=N1 2=N2 3=N3 4=REM 5=Wake 6=Artifact
    probs     : float32 (n_epochs, 6) columns [N1, N2, N3, REM, Wake, ART]

This file must stay importable-free of ScoringHero: it runs in a foreign
interpreter that only has ezscore and its dependencies installed.
"""

import argparse
import json
import os
import sys

# ezscore's models are Keras 2 SavedModels; TF >= 2.16 needs the legacy shim.
os.environ.setdefault("TF_USE_LEGACY_KERAS", "True")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np


def log(message):
    print(message, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    args = parser.parse_args()

    with open(args.job) as handle:
        job = json.load(handle)

    run_job(job)


def run_job(job):
    """Score one recording. Also used in-process when ezscore is importable."""
    log("Importing ezscore ...")
    import mne
    mne.set_log_level("ERROR")
    from ezscore.model_utils import preproc, ezpredict

    data = np.load(job["data_npy"]).astype(np.float64)
    if data.ndim != 2 or data.shape[0] != 2:
        raise ValueError(f"Expected a (2, n_samples) array, got {data.shape}.")

    info = mne.create_info(
        ch_names=["eegl", "eegr"],
        sfreq=float(job["sfreq"]),
        ch_types=["eeg", "eeg"],
    )
    raw = mne.io.RawArray(data, info, verbose=False)

    log("Preprocessing (resample to 64 Hz, high-pass 0.5 Hz) ...")
    data_array, raw = preproc(raw, normalize=bool(job["normalize"]))

    log(f"Loading model from {job['model_dir']} ...")
    from tensorflow.keras.models import load_model
    model = load_model(job["model_dir"], compile=False)

    log("Running inference ...")
    hypnogram, probs = ezpredict(model=model, data=data_array)

    hypnogram = np.asarray(hypnogram, dtype=np.int64).reshape(-1)
    probs = np.asarray(probs, dtype=np.float32).reshape(len(hypnogram), 6)

    np.savez(job["out_npz"], hypnogram=hypnogram, probs=probs)
    log(f"Scored {len(hypnogram)} epochs.")

    summary_png = job.get("summary_png")
    if summary_png:
        try:
            log("Rendering summary figure ...")
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from ezscore.model_utils import ezspectgm, plot_summary

            spectrogram = ezspectgm(raw)
            plot_summary(
                hyp=hypnogram,
                hypdens=probs,
                spctgm_object=spectrogram,
                titl=job.get("title", "ezscore-f"),
            )
            plt.savefig(summary_png, format="png", dpi=130, bbox_inches="tight")
            plt.close("all")
            log("Summary figure written.")
        except Exception as exc:  # a failed figure must not lose the scoring
            log(f"WARNING: could not render the summary figure: {exc}")

    log("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
