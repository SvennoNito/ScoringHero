"""
nidra_env.py — model management for the NIDRA classifiers.

NIDRA (Zerr 2025, https://github.com/paulzerr/nidra) publishes ONNX exports of
the **ezscore-f** models (`ez6`, `ez6moe`, Coon et al. 2025) for two-channel
forehead EEG, with a sixth artifact class.

Because the weights are ONNX rather than TensorFlow SavedModels, ScoringHero
runs them in its own interpreter with `onnxruntime` — no sidecar environment.

This module holds only plain-Python helpers: the model registry, locating and
downloading the weights, and reporting which optional packages are missing.
"""

import os
import sys

# --------------------------------------------------------------------------
# Model registry
# --------------------------------------------------------------------------
MODELS = {
    "ez6": {
        "label":       "ez6 — two-channel forehead EEG",
        "files":       {"default": "ez6.onnx"},
        "size_mb":     12,
        "description": (
            "Artifact-aware 6-class model for forehead montages (ZMax, DCM,\n"
            "CGX PatchEEG). Input is median/IQR normalized."
        ),
    },
    "ez6moe": {
        "label":       "ez6moe — forehead EEG, mixture of experts",
        "files":       {"default": "ez6moe.onnx"},
        "size_mb":     117,
        "description": (
            "Mixture-of-experts variant of ez6: an ensemble of differently\n"
            "trained models. Can be more accurate, but is a ~117 MB download\n"
            "and noticeably slower to load."
        ),
    },
}

DEFAULT_MODEL = "ez6"

# NIDRA's own weight repository
_HF_BASE = "https://huggingface.co/pzerr/NIDRA_models/resolve/main"


def model_files(model_key):
    """Every weight file a model may need, as a list of file names."""
    return list(MODELS[model_key]["files"].values())


def is_frozen():
    """True when running from a packaged build rather than from source."""
    return bool(
        getattr(sys, "frozen", False)
        or hasattr(sys, "_MEIPASS")
        or os.environ.get("NUITKA_ONEFILE_PARENT")
        or "__compiled__" in globals()
    )


# --------------------------------------------------------------------------
# Where the weights live
# --------------------------------------------------------------------------

def default_model_root():
    """ScoringHero's own download location for NIDRA weights."""
    return os.path.join(os.path.expanduser("~"), ".nidra_models")


def nidra_package_model_root():
    """Where a pip-installed NIDRA keeps its models (appdirs.user_data_dir()).

    Checked first, so a user who already runs NIDRA itself never downloads the
    same weights a second time.
    """
    home = os.path.expanduser("~")
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
    elif sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    return os.path.join(base, "NIDRA", "models")


def model_roots(extra_root=""):
    """Directories that may hold NIDRA weights, best first."""
    roots = []
    for root in (extra_root, nidra_package_model_root(), default_model_root()):
        root = (root or "").strip()
        if root and root not in roots:
            roots.append(root)
    return roots


def find_model_file(filename, extra_root=""):
    """Full path of `filename` in the first root that has it, else None.

    A file fetched with huggingface_hub's `local_dir` can end up one level
    deeper in a `models/` sub-folder, so that is checked as well.
    """
    for root in model_roots(extra_root):
        for candidate in (
            os.path.join(root, filename),
            os.path.join(root, "models", filename),
        ):
            if os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
                return os.path.normpath(candidate)
    return None


def missing_model_files(model_key, extra_root=""):
    """Weight files of `model_key` that are not on disk yet."""
    return [
        name for name in model_files(model_key)
        if find_model_file(name, extra_root) is None
    ]


def download_model_file(filename, dest_dir, progress_cb=None):
    """Download one ONNX file from NIDRA's Hugging Face repository.

    progress_cb(downloaded_bytes, total_bytes) is called while downloading;
    returning False from it aborts. The file is staged next to its target and
    renamed only once complete, so a cancelled download never leaves a
    truncated model behind. Returns the path of the downloaded file.
    """
    import requests

    os.makedirs(dest_dir, exist_ok=True)
    target = os.path.join(dest_dir, filename)
    staging = target + ".download"

    try:
        with requests.get(f"{_HF_BASE}/{filename}", stream=True, timeout=60) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length") or 0)
            done = 0
            with open(staging, "wb") as handle:
                for chunk in response.iter_content(chunk_size=1 << 20):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    done += len(chunk)
                    if progress_cb and progress_cb(done, total) is False:
                        raise RuntimeError("Download cancelled.")

        if os.path.exists(target):
            os.remove(target)
        os.rename(staging, target)
    finally:
        if os.path.exists(staging):
            try:
                os.remove(staging)
            except OSError:
                pass

    return target


# --------------------------------------------------------------------------
# Optional dependencies
# --------------------------------------------------------------------------

INSTALL_INSTRUCTIONS = (
    "The NIDRA models run with onnxruntime inside ScoringHero itself, so no\n"
    "second Python environment is needed - but two optional packages are:\n\n"
    "    uv sync --extra nidra\n\n"
    "or, in any environment:\n\n"
    "    pip install onnxruntime mne\n\n"
    "The model weights themselves are downloaded on first use."
)


def missing_requirements():
    """Names of the packages needed for NIDRA that cannot be imported."""
    import importlib.util

    missing = []
    for package in ("onnxruntime", "mne"):
        try:
            if importlib.util.find_spec(package) is None:
                missing.append(package)
        except Exception:
            missing.append(package)
    return missing


def nidra_available():
    """True when NIDRA scoring can run in this interpreter."""
    return not missing_requirements()
