import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PySide6.QtCore import Qt, QTimer

from widgets import SeedWindow
from events.add_events_to_container import add_events_to_container
from scoring.write_scoring import write_scoring
from utilities.refresh_gui import refresh_gui

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

    progress = QProgressDialog("Initializing SEED...", None, 0, 0)
    progress.setWindowTitle("K-Complex / Spindle Detection (SEED)")
    progress.setWindowModality(Qt.WindowModal)
    progress.setCancelButton(None)
    progress.setMinimumDuration(0)
    progress.show()
    progress.raise_()
    QApplication.processEvents()
    QTimer.singleShot(0, lambda: _execute_seed(ui, settings, progress))


def _execute_seed(ui, settings, progress):
    try:
        python_exe = settings["python_exe"]
        seed_dir   = settings["seed_dir"]

        if not os.path.isfile(python_exe):
            raise FileNotFoundError(
                f"SEED Python executable not found:\n{python_exe}\n\n"
                "Please set the correct path in the SEED dialog."
            )

        runner = _find_runner_script()

        channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
        ch_idx    = channel_labels.index(settings["channel"])
        sfreq     = float(ui.config[0]["Sampling_rate_hz"])
        signal_1d = ui.eeg_data_display[ch_idx].copy().astype(np.float32)

        detections = [
            ("detect_kc",       "kc_marker",     "kc",      "K-complex"),
            ("detect_spindles", "spindle_marker", "spindle", "Spindle"),
        ]

        any_added = False
        for detect_key, marker_key, event_type, label in detections:
            if not settings.get(detect_key):
                continue

            progress.setLabelText(f"Running SEED {label} detection…")
            QApplication.processEvents()

            events_sec = _call_seed_subprocess(
                python_exe, runner, seed_dir, signal_1d, sfreq, event_type
            )

            marker_label = settings[marker_key]
            container = next(c for c in ui.AnnotationContainer if c.label == marker_label)
            add_events_to_container(ui, events_sec, container)
            any_added = True

        if not any_added:
            progress.close()
            return

        progress.setLabelText("Finished")
        QApplication.processEvents()

        write_scoring(ui)
        ui.HypnogramWidget.draw_hypnogram(ui)
        refresh_gui(ui)

        QTimer.singleShot(1500, progress.close)

    except Exception as exc:
        import traceback
        tb_str = traceback.format_exc()
        progress.close()
        QMessageBox.critical(
            None,
            "SEED Error",
            f"An error occurred while running SEED:\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            f"Traceback:\n{tb_str}",
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
        np.save(input_f.name, signal_1d)

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


