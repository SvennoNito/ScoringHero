"""
ezscore_env.py — environment and model management for the ezscore-f classifier.

ezscore-f (Coon et al. 2025, doi:10.1101/2025.06.02.657451) is a set of
artifact-aware sleep stage classifiers for two-channel forehead EEG. The
package pins TensorFlow 2.15 and only supports Python 3.9-3.11, so it cannot
be installed into ScoringHero's own environment (Python >= 3.13). ScoringHero
therefore calls it out-of-process, the same way it calls SEED.

This module contains only plain-Python helpers (no TensorFlow, no Qt widgets):
locating the sidecar interpreter, locating/downloading the model weights, and
describing the available model variants.
"""

import os
import sys

# --------------------------------------------------------------------------
# Model variants
# --------------------------------------------------------------------------
# "normalize" mirrors the `normalize` flag of ezscore.model_utils.preproc:
#   True  -> median/IQR normalized input (offline models ez6 / ez6moe)
#   False -> raw microvolt input         (real-time model ez6rt)

MODEL_VARIANTS = {
    "ez6": {
        "label":       "ez6 — offline (normalized input)",
        "normalize":   True,
        "size_mb":     37,
        "description": (
            "Artifact-aware 6-class model for offline analysis. Operates on\n"
            "median/IQR-normalized EEG. Best overall accuracy of the two\n"
            "lightweight models (81.3 %, Cohen's kappa 0.74 in the paper)."
        ),
    },
    "ez6rt": {
        "label":       "ez6rt — real-time (raw µV input)",
        "normalize":   False,
        "size_mb":     37,
        "description": (
            "Artifact-aware 6-class model trained on raw microvolt amplitudes,\n"
            "intended for real-time use. Slightly lower overall accuracy than\n"
            "ez6 (79.2 %, kappa 0.71) but does not require whole-night statistics."
        ),
    },
    "ez6moe": {
        "label":       "ez6moe — mixture of experts (normalized input)",
        "normalize":   True,
        "size_mb":     377,
        "description": (
            "Mixture-of-experts model that averages the predictions of an\n"
            "ensemble of differently trained ez6 models. Can be more accurate\n"
            "but is a ~377 MB download and loads considerably more slowly."
        ),
    },
}

DEFAULT_VARIANT = "ez6"

# Files that make up a TensorFlow SavedModel directory
_MODEL_FILES = [
    "saved_model.pb",
    "fingerprint.pb",
    "keras_metadata.pb",
    "variables/variables.index",
    "variables/variables.data-00000-of-00001",
]

_GITHUB_BASE = "https://raw.githubusercontent.com/coonwg1/ezscore/main/model"
_HF_BASE     = "https://huggingface.co/coonwg1/ez6moe/resolve/main/ez6moe"


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------

def default_model_root():
    """Directory ezscore itself uses for downloaded models (~/.ezscore_models)."""
    return os.path.join(os.path.expanduser("~"), ".ezscore_models")


def is_model_dir(path):
    """True if `path` is a *complete* TensorFlow SavedModel directory.

    The weights matter as much as the graph: checking only saved_model.pb would
    accept a half-finished download and fail later inside TensorFlow with an
    unhelpful message.
    """
    if not path or not os.path.isdir(path):
        return False
    if not os.path.isfile(os.path.join(path, "saved_model.pb")):
        return False

    variables = os.path.join(path, "variables")
    if not os.path.isfile(os.path.join(variables, "variables.index")):
        return False
    try:
        return any(
            name.startswith("variables.data-") for name in os.listdir(variables)
        )
    except OSError:
        return False


def find_model_dir(variant, extra_roots=None):
    """Return the first existing SavedModel directory for `variant`, else None.

    Searched, in order: any caller-supplied root (e.g. the `model/` folder of a
    cloned ezscore repository), then ~/.ezscore_models.
    """
    candidates = []
    for root in (extra_roots or []):
        if not root:
            continue
        candidates.append(root)                       # root is the model dir itself
        candidates.append(os.path.join(root, variant))  # root contains ez6/, ez6rt/, ...
    root = default_model_root()
    candidates.append(os.path.join(root, variant))
    # ezscore's own huggingface download nests the model one level deeper
    candidates.append(os.path.join(root, variant, variant))

    for candidate in candidates:
        if is_model_dir(candidate):
            return os.path.normpath(candidate)
    return None


def model_file_urls(variant):
    """Return [(url, relative_path), ...] for every file of a model variant."""
    if variant == "ez6moe":
        base = _HF_BASE
    else:
        base = f"{_GITHUB_BASE}/{variant}"
    return [(f"{base}/{name}", name) for name in _MODEL_FILES]


def download_model(variant, dest_dir, progress_cb=None):
    """Download a model variant into `dest_dir`.

    progress_cb(file_index, n_files, downloaded_bytes, total_bytes) is called
    while downloading; returning False from it aborts the download.
    Raises on failure. Returns `dest_dir` on success.
    """
    import requests
    import shutil

    urls = model_file_urls(variant)

    # Download into a staging folder and move it into place only once every
    # file has arrived, so a cancelled download never leaves behind a directory
    # that looks like a usable model.
    staging = dest_dir + ".download"
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging, exist_ok=True)

    try:
        for index, (url, relative) in enumerate(urls):
            target = os.path.join(staging, relative.replace("/", os.sep))
            os.makedirs(os.path.dirname(target), exist_ok=True)

            with requests.get(url, stream=True, timeout=60) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length") or 0)
                done = 0
                with open(target, "wb") as handle:
                    for chunk in response.iter_content(chunk_size=1 << 20):
                        if not chunk:
                            continue
                        handle.write(chunk)
                        done += len(chunk)
                        if progress_cb and progress_cb(index, len(urls), done, total) is False:
                            raise RuntimeError("Download cancelled.")

        if not is_model_dir(staging):
            raise RuntimeError(
                f"The download of '{variant}' finished but is missing files."
            )

        shutil.rmtree(dest_dir, ignore_errors=True)
        os.makedirs(os.path.dirname(dest_dir) or ".", exist_ok=True)
        os.rename(staging, dest_dir)

    finally:
        shutil.rmtree(staging, ignore_errors=True)

    return dest_dir


# --------------------------------------------------------------------------
# Sidecar interpreter
# --------------------------------------------------------------------------

def _python_in(venv_dir):
    if os.name == "nt":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    return os.path.join(venv_dir, "bin", "python")


def is_frozen():
    """True when running from a packaged build rather than from source."""
    return bool(
        getattr(sys, "frozen", False)
        or hasattr(sys, "_MEIPASS")
        or os.environ.get("NUITKA_ONEFILE_PARENT")
        or "__compiled__" in globals()
    )


def default_environment_dir(app_path=None):
    """Where a new ezscore environment should be created.

    In a build `app_path` is a temporary extraction directory, so the
    environment goes next to the executable instead — that is also where
    autodetect_python() looks for it.
    """
    base = os.path.dirname(os.path.abspath(sys.executable)) if is_frozen() else (app_path or os.getcwd())
    return os.path.join(base, VENV_NAME)


def environment_roots(app_path=None):
    """Directories that may hold the ezscore virtual environment, best first.

    For a build this must include the folder of the .exe itself: `app_path` is
    the temporary extraction directory there, not a place the user can install
    anything into.
    """
    roots = []
    for root in (
        app_path,
        os.path.dirname(os.path.abspath(sys.executable)),
        os.getcwd(),
    ):
        if root and root not in roots:
            roots.append(root)
    return roots


def autodetect_python(app_path=None):
    """Best guess at a Python interpreter that has ezscore installed.

    Looks at $EZSCORE_PYTHON, then at conventional virtual-environment
    directories next to the application. Returns a path or "".
    """
    from_env = os.environ.get("EZSCORE_PYTHON", "").strip()
    if from_env and os.path.isfile(from_env):
        return from_env

    for root in environment_roots(app_path):
        for name in (".venv_ezscore", ".venv_ez", "venv_ezscore"):
            candidate = _python_in(os.path.join(root, name))
            if os.path.isfile(candidate):
                return candidate
    return ""


def ezscore_importable():
    """True if ezscore can be imported in *this* interpreter (rare: needs py<3.12)."""
    if sys.version_info >= (3, 12):
        return False
    try:
        import importlib.util
        return importlib.util.find_spec("ezscore") is not None
    except Exception:
        return False


SETUP_INSTRUCTIONS = (
    "ezscore-f pins TensorFlow 2.15 and supports Python 3.9-3.11 only, so it\n"
    "cannot be installed into ScoringHero's own environment. ScoringHero runs\n"
    "it in a separate interpreter instead.\n\n"
    "Press 'Set up ezscore environment...' below to create one automatically\n"
    "(this needs uv and downloads about 1 GB), or build it yourself:\n\n"
    "    uv venv .venv_ezscore --python 3.11\n"
    "    uv pip install --python .venv_ezscore ezscore\n\n"
    "ScoringHero picks up '.venv_ezscore' next to the application automatically;\n"
    "otherwise point the field above at that environment's python.exe."
)


# --------------------------------------------------------------------------
# Creating the sidecar environment
# --------------------------------------------------------------------------

PYTHON_VERSION = "3.11"
VENV_NAME = ".venv_ezscore"

# ezscore's own dependency list minus keras_nlp. keras_nlp 0.9.3 requires
# tensorflow-text, which publishes no Windows wheels compatible with
# TensorFlow 2.15, and nothing in ezscore's inference path imports keras_nlp —
# so where the plain install fails we install the rest and add ezscore
# with --no-deps.
FALLBACK_DEPENDENCIES = [
    "tensorflow==2.15",
    "tf_keras",
    "huggingface-hub>=0.33.1",
    "mne",
    "pandas",
    "numpy",
    "scikit-learn",
    "matplotlib",
    "seaborn",
    "lspopt",
]

UV_INSTRUCTIONS = (
    "uv was not found. It is needed to create the ezscore environment "
    "because it can fetch Python 3.11 on its own.\n\n"
    "Install it from https://docs.astral.sh/uv/getting-started/installation/ "
    "(on Windows:\n"
    '    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"\n'
    ")\nand try again."
)


def find_uv():
    """Path to the uv executable, or "" when it is not installed."""
    import shutil

    found = shutil.which("uv")
    if found:
        return found

    home = os.path.expanduser("~")
    name = "uv.exe" if os.name == "nt" else "uv"
    for candidate in (
        os.path.join(home, ".local", "bin", name),
        os.path.join(home, ".cargo", "bin", name),
    ):
        if os.path.isfile(candidate):
            return candidate
    return ""


def _run(command, on_output=None):
    """Run a command, streaming its output. Returns (returncode, output)."""
    import subprocess

    if on_output:
        on_output("$ " + " ".join(command))

    # ScoringHero's own interpreter must not leak into the new environment
    env = os.environ.copy()
    for name in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME", "UV_PROJECT_ENVIRONMENT"):
        env.pop(name, None)

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
        creationflags=creationflags,
    )

    collected = []
    for line in process.stdout:
        line = line.rstrip()
        collected.append(line)
        if on_output and line:
            on_output(line)
    process.wait()
    return process.returncode, "\n".join(collected)


def create_environment(venv_dir, on_output=None, python_version=PYTHON_VERSION):
    """Create `venv_dir` with ezscore installed and return its interpreter.

    Idempotent: an existing, working environment is returned as-is. Raises
    RuntimeError with a readable message when something goes wrong.
    """
    interpreter = _python_in(venv_dir)
    if os.path.isfile(interpreter):
        if on_output:
            on_output(f"Environment already exists: {venv_dir}")
    else:
        uv = find_uv()
        if not uv:
            raise RuntimeError(UV_INSTRUCTIONS)

        code, output = _run([uv, "venv", venv_dir, "--python", python_version], on_output)
        if code != 0:
            raise RuntimeError(f"Could not create {venv_dir}:\n\n{output[-2000:]}")

        installer = [uv, "pip", "install", "--python", interpreter]
        code, output = _run(installer + ["ezscore"], on_output)
        if code != 0:
            if on_output:
                on_output(
                    "The standard install failed (expected on Windows, where "
                    "keras_nlp's tensorflow-text dependency has no wheels). "
                    "Installing ezscore without keras_nlp instead."
                )
            code, output = _run(installer + FALLBACK_DEPENDENCIES, on_output)
            if code != 0:
                raise RuntimeError(f"Installing ezscore's dependencies failed:\n\n{output[-2000:]}")
            code, output = _run(installer + ["--no-deps", "ezscore"], on_output)
            if code != 0:
                raise RuntimeError(f"Installing ezscore failed:\n\n{output[-2000:]}")

    code, output = _run(
        [interpreter, "-c", "import ezscore, tensorflow; print(tensorflow.__version__)"],
        on_output,
    )
    if code != 0:
        raise RuntimeError(f"ezscore cannot be imported in {venv_dir}:\n\n{output[-2000:]}")

    return interpreter
