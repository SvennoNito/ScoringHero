import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PySide6.QtWidgets import QMessageBox

from widgets import SeedWindow
from event_detection.run_detector import DetectorSpec
from event_detection.run_detector_gui import run_event_detector

_SETTINGS_FILE = "seed_settings.json"


def _settings_path(ui):
    return os.path.join(ui.app_path, _SETTINGS_FILE)


def _load_seed_settings(ui):
    path = _settings_path(ui)
    if os.path.isfile(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {"python_exe": "", "seed_dir": ""}


def _save_seed_settings(ui, settings):
    path = _settings_path(ui)
    try:
        with open(path, "w") as f:
            json.dump({"python_exe": settings["python_exe"],
                       "seed_dir":   settings["seed_dir"]}, f, indent=2)
    except Exception:
        pass


def open_seed_window(ui):
    if not hasattr(ui, "eeg_data_display") or ui.eeg_data_display is None:
        QMessageBox.warning(None, "No data loaded", "Please load EEG data first.")
        return

    channel_labels    = [ch["Channel_name"] for ch in ui.config[1]]
    annotation_labels = [c.label for c in ui.AnnotationContainer]
    saved             = _load_seed_settings(ui)

    ui.SeedWindow = SeedWindow(channel_labels, annotation_labels, saved)
    ui.SeedWindow.settingsAccepted.connect(
        lambda settings: _after_seed_settings(ui, settings)
    )
    ui.SeedWindow.show()


def _after_seed_settings(ui, settings):
    _save_seed_settings(ui, settings)

    detections = [
        ("detect_kc",       "kc_marker",      "kc",      "K-complex"),
        ("detect_spindles", "spindle_marker", "spindle", "Spindle"),
    ]
    for detect_key, marker_key, event_type, label in detections:
        if not settings.get(detect_key):
            continue
        spec = DetectorSpec(
            detect=lambda signal, sfreq, event_type=event_type: _detect_seed(
                settings["python_exe"], settings["seed_dir"], signal, sfreq, event_type
            ),
            args=lambda s: {},
            method="SEED",
            title="K-Complex / Spindle Detection (SEED)",
            noun=label,
        )
        run_settings = {"channel": settings["channel"], "marker": settings[marker_key]}
        if not run_event_detector(ui, spec, run_settings):
            break


def _detect_seed(python_exe, seed_dir, signal_1d, sfreq, event_type):
    if not os.path.isfile(python_exe):
        raise FileNotFoundError(
            f"SEED Python executable not found:\n{python_exe}\n\n"
            "Please set the correct path in the SEED dialog."
        )
    return _call_seed_subprocess(
        python_exe, _find_runner_script(), seed_dir, signal_1d, sfreq, event_type
    )


def _find_runner_script():
    """Return path to seed_runner.py whether running from source or as a PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        # PyInstaller extracts data files into sys._MEIPASS
        path = os.path.join(sys._MEIPASS, "seed_runner.py")
    else:
        path = os.path.join(os.path.dirname(__file__), "seed_runner.py")

    if not os.path.isfile(path):
        raise FileNotFoundError(f"seed_runner.py not found at: {path}")
    return path


def _call_seed_subprocess(python_exe, runner, seed_dir, signal_1d, sfreq, event_type):
    input_f  = tempfile.NamedTemporaryFile(suffix=".npy",  delete=False)
    output_f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    input_f.close()
    output_f.close()

    try:
        np.save(input_f.name, signal_1d.astype(np.float32))

        result = subprocess.run(
            [
                python_exe, runner,
                "--seed_dir",   seed_dir,
                "--input",      input_f.name,
                "--sfreq",      str(sfreq),
                "--event_type", event_type,
                "--output",     output_f.name,
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"SEED subprocess failed (exit {result.returncode}):\n\n"
                f"{result.stderr or result.stdout}"
            )

        with open(output_f.name) as f:
            return json.load(f)

    finally:
        for p in (input_f.name, output_f.name):
            try:
                os.unlink(p)
            except OSError:
                pass


