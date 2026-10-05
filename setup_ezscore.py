"""
setup_ezscore.py — create the sidecar environment ScoringHero uses for ezscore-f.

ezscore-f pins TensorFlow 2.15 and supports Python 3.9-3.11 only, so it cannot
live in ScoringHero's own environment (Python >= 3.13). This script creates
`.venv_ezscore` next to ScoringHero, installs ezscore into it, and downloads a
model. ScoringHero picks `.venv_ezscore` up automatically.

    python setup_ezscore.py                 # env + the default ez6 model
    python setup_ezscore.py --model ez6rt   # a different model variant
    python setup_ezscore.py --no-model      # environment only

The same thing is available from inside the application: Autoscore -> Forehead
EEG Classifier (ezscore-f) -> "Set up ezscore environment...". Both call
scoring/ezscore_env.py, so a packaged .exe needs no copy of this script.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, HERE)
from scoring.ezscore_env import (  # noqa: E402
    MODEL_VARIANTS,
    DEFAULT_VARIANT,
    VENV_NAME,
    create_environment,
    default_model_root,
    download_model,
    find_model_dir,
)

VENV_DIR = os.path.join(HERE, VENV_NAME)


def fetch_model(variant):
    existing = find_model_dir(variant)
    if existing:
        print(f"\nModel '{variant}' already available: {existing}")
        return existing

    target = os.path.join(default_model_root(), variant)
    size = MODEL_VARIANTS[variant]["size_mb"]
    print(f"\nDownloading model '{variant}' (~{size} MB) to {target} ...")

    state = {"file": -1}

    def report(index, n_files, done, total):
        if index != state["file"]:
            state["file"] = index
            print(f"  file {index + 1}/{n_files}")
        if total:
            percent = 100 * done / total
            print(f"\r    {done / (1 << 20):7.1f} MB  ({percent:5.1f} %)", end="", flush=True)
        return True

    download_model(variant, target, progress_cb=report)
    print("\n  done.")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default=DEFAULT_VARIANT,
        choices=sorted(MODEL_VARIANTS),
        help=f"model variant to download (default: {DEFAULT_VARIANT})",
    )
    parser.add_argument("--no-model", action="store_true", help="skip the model download")
    args = parser.parse_args()

    try:
        interpreter = create_environment(VENV_DIR, on_output=print)
    except RuntimeError as exc:
        raise SystemExit(f"\n{exc}")

    if not args.no_model:
        fetch_model(args.model)

    print(
        "\nDone. Start ScoringHero and use Autoscore -> Forehead EEG Classifier "
        "(ezscore-f).\nThe interpreter below is detected automatically:\n"
        f"  {interpreter}"
    )


if __name__ == "__main__":
    main()
