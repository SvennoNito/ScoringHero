"""
ezscore_runner.py — drives the ezscore-f classifier from ScoringHero.

ezscore normally lives in its own interpreter (see ezscore_env.py), so the
work is handed to `ezscore_worker.py` as a subprocess. When ScoringHero itself
happens to run on a Python that can import ezscore, the same job is executed
in-process instead.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np

from .ezscore_env import ezscore_importable


class EzscoreCancelled(Exception):
    """Raised when the user aborts a running ezscore job."""


def _worker_candidates():
    """Every place ezscore_worker.py may sit, from source or from a build.

    Nuitka keeps the compiled module's __file__ inside the extraction folder, so
    the data file bundled as `scoring/ezscore_worker.py` lands next to it. The
    remaining candidates cover PyInstaller and a worker shipped beside the .exe.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    yield os.path.join(here, "ezscore_worker.py")

    roots = [
        getattr(sys, "_MEIPASS", None),
        os.path.dirname(here),
        os.path.dirname(os.path.abspath(sys.executable)),
    ]
    for root in roots:
        if not root:
            continue
        yield os.path.join(root, "scoring", "ezscore_worker.py")
        yield os.path.join(root, "ezscore_worker.py")


def _find_worker_script():
    """Path to ezscore_worker.py, whether running from source or frozen."""
    checked = []
    for path in _worker_candidates():
        if path in checked:
            continue
        if os.path.isfile(path):
            return path
        checked.append(path)

    raise FileNotFoundError(
        "ezscore_worker.py could not be found. Looked in:\n  "
        + "\n  ".join(checked)
        + "\n\nIn a build it must be included as a data file, e.g. Nuitka:\n"
        "  --include-data-files=./scoring/ezscore_worker.py=scoring/ezscore_worker.py"
    )


def _tail(path, n_lines=1):
    """Last `n_lines` non-empty lines of a log file (empty string if unreadable)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = [line.rstrip() for line in handle if line.strip()]
    except OSError:
        return ""
    return "\n".join(lines[-n_lines:])


def run_ezscore(
    data_volts,
    sfreq,
    model_dir,
    normalize,
    python_exe="",
    summary_png=None,
    title="ezscore-f",
    tick=None,
    timeout=3600,
):
    """Run ezscore-f on a two-channel forehead montage.

    Parameters
    ----------
    data_volts : array (2, n_samples)
        Left and right forehead EEG in VOLTS (ezscore's own convention).
    sfreq : float
        Sampling rate of `data_volts`; ezscore resamples to 64 Hz itself.
    model_dir : str
        TensorFlow SavedModel directory (ez6, ez6rt or ez6moe).
    normalize : bool
        Median/IQR normalization — True for ez6/ez6moe, False for ez6rt.
    python_exe : str
        Interpreter of the ezscore environment. Empty means "run in-process",
        which is only valid when ezscore is importable here.
    summary_png : str or None
        Where to write ezscore's hypnogram/hypnodensity/spectrogram figure.
    tick : callable or None
        Called repeatedly with the newest worker log line while the subprocess
        runs. Returning False cancels the run.

    Returns
    -------
    hypnogram : int array (n_epochs,)
        1=N1, 2=N2, 3=N3, 4=REM, 5=Wake, 6=Artifact — one value per 30 s epoch.
    probs : float array (n_epochs, 6)
        Class probabilities, columns [N1, N2, N3, REM, Wake, ART].
    """
    workdir = tempfile.mkdtemp(prefix="scoringhero_ezscore_")
    try:
        data_npy = os.path.join(workdir, "data.npy")
        out_npz = os.path.join(workdir, "result.npz")
        job_path = os.path.join(workdir, "job.json")
        log_path = os.path.join(workdir, "ezscore.log")

        # float32 halves the size of the hand-over file; the worker casts back
        # to float64 before building the MNE Raw object.
        np.save(data_npy, np.ascontiguousarray(data_volts, dtype=np.float32))

        job = {
            "data_npy":    data_npy,
            "sfreq":       float(sfreq),
            "model_dir":   model_dir,
            "normalize":   bool(normalize),
            "out_npz":     out_npz,
            "summary_png": summary_png,
            "title":       title,
        }
        with open(job_path, "w") as handle:
            json.dump(job, handle)

        if python_exe:
            _run_subprocess(python_exe, job_path, log_path, tick, timeout)
        elif ezscore_importable():
            from .ezscore_worker import run_job
            run_job(job)
        else:
            raise RuntimeError(
                "No ezscore environment configured and ezscore cannot be "
                "imported in ScoringHero's own interpreter."
            )

        if not os.path.isfile(out_npz):
            raise RuntimeError(
                "ezscore finished without writing any results.\n\n"
                + (_tail(log_path, 20) or "(no output captured)")
            )

        with np.load(out_npz) as result:
            hypnogram = result["hypnogram"].astype(int)
            probs = result["probs"].astype(float)

        return hypnogram, probs

    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _run_subprocess(python_exe, job_path, log_path, tick, timeout):
    if not os.path.isfile(python_exe):
        raise FileNotFoundError(
            f"ezscore Python executable not found:\n{python_exe}\n\n"
            "Set the correct path in the ezscore-f dialog."
        )

    worker = _find_worker_script()

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PYTHONUNBUFFERED"] = "1"

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

    with open(log_path, "w", encoding="utf-8", errors="replace") as logfile:
        process = subprocess.Popen(
            [python_exe, worker, "--job", job_path],
            stdout=logfile,
            stderr=subprocess.STDOUT,
            env=env,
            creationflags=creationflags,
        )

        started = time.monotonic()
        while process.poll() is None:
            if tick is not None and tick(_tail(log_path)) is False:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                raise EzscoreCancelled()

            if time.monotonic() - started > timeout:
                process.kill()
                raise TimeoutError(
                    f"ezscore did not finish within {timeout} s.\n\n"
                    + (_tail(log_path, 20) or "(no output captured)")
                )

            time.sleep(0.15)

    if process.returncode != 0:
        raise RuntimeError(
            f"The ezscore subprocess failed (exit code {process.returncode}):\n\n"
            + (_tail(log_path, 30) or "(no output captured)")
        )
