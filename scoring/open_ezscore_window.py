"""
open_ezscore_window.py — GUI flow for automatic sleep staging with ezscore-f.

ezscore-f (Coon et al. 2025, doi:10.1101/2025.06.02.657451) classifies
two-channel forehead EEG into Wake, N1, N2, N3, REM and a sixth artifact
class. The heavy lifting happens in ezscore_runner/ezscore_worker; this module
only collects settings, applies the result to ui.stages and reports progress.
"""

import json
import os
import sys
import tempfile

import numpy as np
from PySide6.QtWidgets import (
    QMessageBox, QProgressDialog, QApplication,
)
from PySide6.QtCore import Qt, QTimer

from widgets import EzscoreWindow, EzscoreSummaryWindow
from events.add_events_to_container import add_events_to_container
from utilities.refresh_gui import refresh_gui
from .ezscore_env import (
    MODEL_VARIANTS,
    autodetect_python,
    default_model_root,
    download_model,
    find_model_dir,
    is_frozen,
    is_model_dir,
)
from .ezscore_runner import EzscoreCancelled, run_ezscore
from .write_scoring import write_scoring

_SETTINGS_FILE = "ezscore_settings.json"

# ezscore hypnogram codes -> ScoringHero (stage, digit). 6 = artifact, handled apart.
_STAGE_MAP = {
    1: ("N1",   -1),
    2: ("N2",   -2),
    3: ("N3",   -3),
    4: ("REM",   0),
    5: ("Wake",  1),
}

# Column order of the probability matrix returned by ezpredict
_PROB_COLUMNS = ["N1", "N2", "N3", "REM", "Wake", "ART"]

_ARTIFACT_CODE = 6


# --------------------------------------------------------------------------
# Persisted settings
# --------------------------------------------------------------------------

def _settings_paths(ui):
    """Where the ezscore settings live, most preferred first.

    In a build `ui.app_path` is a temporary extraction directory that is wiped
    when the app closes, so the file goes next to the executable instead, with
    the user's home directory as a fallback for read-only install locations.
    """
    directories = []
    if is_frozen():
        directories.append(os.path.dirname(os.path.abspath(sys.executable)))
    else:
        directories.append(ui.app_path)
    directories.append(os.path.join(os.path.expanduser("~"), ".scoringhero"))

    return [os.path.join(directory, _SETTINGS_FILE) for directory in directories]


def _load_settings(ui):
    settings = {}
    for path in _settings_paths(ui):
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as handle:
                settings = json.load(handle)
            break
        except Exception:
            continue

    if not settings.get("python_exe"):
        settings["python_exe"] = autodetect_python(ui.app_path)
    return settings


def _save_settings(ui, settings):
    for path in _settings_paths(ui):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as handle:
                json.dump(settings, handle, indent=2)
            return
        except Exception:
            continue


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def open_ezscore_window(ui):
    if not hasattr(ui, "eeg_data_display") or ui.eeg_data_display is None:
        QMessageBox.warning(None, "No data loaded", "Please load EEG data first.")
        return

    # Keep the name->index cache in step with the current channel config: a
    # channel added or renamed in the config window may not have refreshed it
    # yet (the rename is debounced), which would make the channel lookup in
    # _execute_ezscore() fail on a channel the dialog happily offers.
    from utilities.channel_index import rebuild_channel_index
    rebuild_channel_index(ui)

    channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
    annotation_labels = [container.label for container in ui.AnnotationContainer]

    ui.EzscoreWindow = EzscoreWindow(
        channel_labels,
        annotation_labels,
        saved=_load_settings(ui),
        app_path=ui.app_path,
    )
    ui.EzscoreWindow.settingsAccepted.connect(
        lambda settings: _after_ezscore_settings(ui, settings)
    )
    ui.EzscoreWindow.show()


def _after_ezscore_settings(ui, settings):
    _save_settings(ui, settings)

    # Step A: epoch length
    epolen = ui.config[0]["Epoch_length_s"]
    if epolen != 30:
        message = QMessageBox()
        message.setIcon(QMessageBox.Warning)
        message.setWindowTitle("Epoch length mismatch")
        message.setText(
            f"ezscore-f uses 30-second epochs, but your epoch length is {epolen}s.\n\n"
            "ezscore scores will be mapped onto your epoch grid automatically.\n\n"
            "You can adjust the epoch length in the Configuration panel "
            "if you prefer 30s epochs."
        )
        continue_button = message.addButton("Continue", QMessageBox.AcceptRole)
        message.addButton("Cancel", QMessageBox.RejectRole)
        message.exec()
        if message.clickedButton() != continue_button:
            return

    # Step B: existing scores
    scored_count = sum(1 for epoch in ui.stages if epoch["stage"] is not None)
    mode = "overwrite"
    overwrite_stages = None

    if scored_count > 0:
        from .open_gssc_window import _ask_selective_stages

        message = QMessageBox()
        message.setIcon(QMessageBox.Warning)
        message.setWindowTitle("Existing scores detected")
        message.setText(
            f"{scored_count} epoch(s) already have sleep scores.\n"
            "How would you like to proceed?"
        )
        overwrite_button = message.addButton("Overwrite all", QMessageBox.AcceptRole)
        selective_button = message.addButton("Overwrite selected stages...", QMessageBox.AcceptRole)
        fill_button = message.addButton("Fill missing only", QMessageBox.AcceptRole)
        message.addButton("Cancel", QMessageBox.RejectRole)
        message.exec()

        clicked = message.clickedButton()
        if clicked == overwrite_button:
            mode = "overwrite"
        elif clicked == selective_button:
            overwrite_stages = _ask_selective_stages()
            if overwrite_stages is None:
                return
            mode = "selective"
        elif clicked == fill_button:
            mode = "fill_missing"
        else:
            return

    # Step C: model weights
    model_dir = _ensure_model(ui, settings)
    if model_dir is None:
        return

    # Step D: run
    progress = QProgressDialog("Starting ezscore-f...", "Cancel", 0, 0)
    progress.setWindowTitle("Auto Score (ezscore-f)")
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)
    progress.setAutoClose(False)
    progress.setAutoReset(False)
    progress.show()
    progress.raise_()
    QApplication.processEvents()

    QTimer.singleShot(
        0,
        lambda: _execute_ezscore(ui, settings, model_dir, mode, overwrite_stages, progress),
    )


# --------------------------------------------------------------------------
# Model weights
# --------------------------------------------------------------------------

def _ensure_model(ui, settings):
    """Return a usable SavedModel directory, downloading it if the user agrees."""
    variant = settings["variant"]
    typed = settings.get("model_dir", "").strip()

    if typed:
        if is_model_dir(typed):
            return typed
        nested = os.path.join(typed, variant)
        if is_model_dir(nested):
            return nested
    else:
        found = find_model_dir(variant)
        if found:
            return found

    spec = MODEL_VARIANTS.get(variant, {})
    target = os.path.join(typed or default_model_root(), variant)

    answer = QMessageBox.question(
        None,
        "Download ezscore model",
        f"The ezscore model '{variant}' was not found.\n\n"
        f"Download it now (about {spec.get('size_mb', '?')} MB) to:\n{target}",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes,
    )
    if answer != QMessageBox.Yes:
        return None

    progress = QProgressDialog(f"Downloading '{variant}'...", "Cancel", 0, 100)
    progress.setWindowTitle("Download ezscore model")
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)
    progress.setAutoClose(False)
    progress.setAutoReset(False)
    progress.show()
    QApplication.processEvents()

    def on_progress(index, n_files, done, total):
        megabytes = done / (1 << 20)
        if total:
            progress.setValue(int(100 * done / total))
            progress.setLabelText(
                f"Downloading '{variant}' — file {index + 1} of {n_files} "
                f"({megabytes:.1f} of {total / (1 << 20):.1f} MB)"
            )
        else:
            progress.setLabelText(
                f"Downloading '{variant}' — file {index + 1} of {n_files} ({megabytes:.1f} MB)"
            )
        QApplication.processEvents()
        return not progress.wasCanceled()

    try:
        download_model(variant, target, progress_cb=on_progress)
    except Exception as exc:
        progress.close()
        if progress.wasCanceled():
            return None
        QMessageBox.critical(
            None,
            "Download failed",
            f"The ezscore model could not be downloaded:\n\n{type(exc).__name__}: {exc}",
        )
        return None

    progress.close()
    return target


# --------------------------------------------------------------------------
# Inference
# --------------------------------------------------------------------------

def _execute_ezscore(ui, settings, model_dir, mode, overwrite_stages, progress):
    summary_png = None
    try:
        left_index = ui.channel_name_to_idx.get(settings["left_channel"])
        if left_index is None:
            raise ValueError(f"Unknown channel: {settings['left_channel']}")

        if settings["duplicate_left"]:
            right_index = left_index
            channels_used = [settings["left_channel"]]
        else:
            right_index = ui.channel_name_to_idx.get(settings["right_channel"])
            if right_index is None:
                raise ValueError(f"Unknown channel: {settings['right_channel']}")
            channels_used = [settings["left_channel"], settings["right_channel"]]

        # ScoringHero keeps its signals in microvolts; ezscore expects volts.
        data_volts = np.vstack([
            ui.eeg_data_display[left_index],
            ui.eeg_data_display[right_index],
        ]).astype(np.float64) / 1e6

        sfreq = float(ui.config[0]["Sampling_rate_hz"])
        variant = settings["variant"]
        normalize = MODEL_VARIANTS[variant]["normalize"]

        if settings["show_summary"]:
            handle = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            handle.close()
            summary_png = handle.name

        def tick(latest_line):
            progress.setLabelText(latest_line or "Running ezscore-f...")
            QApplication.processEvents()
            return not progress.wasCanceled()

        hypnogram, probabilities = run_ezscore(
            data_volts,
            sfreq,
            model_dir,
            normalize,
            python_exe=settings.get("python_exe", ""),
            summary_png=summary_png,
            title=variant,
            tick=tick,
        )

        n_artifact = _apply_scores(
            ui, settings, hypnogram, probabilities, channels_used, mode, overwrite_stages
        )

        progress.setLabelText(f"Finished — {len(hypnogram)} epochs scored.")
        QApplication.processEvents()

        write_scoring(ui)
        ui.HypnogramWidget.draw_hypnogram(ui)
        refresh_gui(ui)

        QTimer.singleShot(1200, progress.close)

        if summary_png and os.path.isfile(summary_png):
            ui.EzscoreSummaryWindow = EzscoreSummaryWindow(summary_png)
            ui.EzscoreSummaryWindow.show()
            summary_png = None  # the window keeps reading the file

        if n_artifact:
            QTimer.singleShot(
                1300,
                lambda: QMessageBox.information(
                    None,
                    "ezscore-f finished",
                    f"{n_artifact} of {len(hypnogram)} epoch(s) were classified as artifact "
                    "and handled according to your artifact setting.",
                ),
            )

    except EzscoreCancelled:
        progress.close()

    except Exception as exc:
        import traceback
        traceback_text = traceback.format_exc()
        progress.close()
        QMessageBox.critical(
            None,
            "ezscore-f Error",
            f"An error occurred while running ezscore-f:\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            f"Traceback:\n{traceback_text}",
        )

    finally:
        if summary_png and os.path.isfile(summary_png):
            try:
                os.unlink(summary_png)
            except OSError:
                pass


def _apply_scores(ui, settings, hypnogram, probabilities, channels_used, mode, overwrite_stages):
    """Write the ezscore result into ui.stages. Returns the artifact epoch count."""
    epolen = ui.config[0]["Epoch_length_s"]
    variant = settings["variant"]
    source = f"ezscore-f ({variant})"
    artifact_mode = settings["artifact_mode"]
    store_probabilities = settings["store_probabilities"]

    artifact_intervals = []

    for index, epoch in enumerate(ui.stages):
        if mode == "fill_missing" and epoch["stage"] is not None:
            continue
        if mode == "selective" and epoch["stage"] not in overwrite_stages:
            continue

        if epolen == 30:
            ez_index = index
        else:
            midpoint = (epoch["start"] + epoch["end"]) / 2.0
            ez_index = int(midpoint // 30)

        if ez_index < 0 or ez_index >= len(hypnogram):
            continue

        code = int(hypnogram[ez_index])
        confidence = round(float(probabilities[ez_index, code - 1]), 4)

        if code == _ARTIFACT_CODE:
            artifact_intervals.append([epoch["start"], epoch["end"]])
            epoch["clean"] = 0
            if artifact_mode == "inconclusive":
                epoch["stage"] = "Inconclusive"
                epoch["digit"] = 2
            else:
                epoch["stage"] = None
                epoch["digit"] = None
            epoch["source"] = f"{source} — artifact"
        else:
            stage_name, digit = _STAGE_MAP[code]
            epoch["stage"] = stage_name
            epoch["digit"] = digit
            epoch["source"] = source

        epoch["confidence"] = confidence
        epoch["channels"] = channels_used

        if store_probabilities:
            epoch["probabilities"] = {
                name: round(float(probabilities[ez_index, column]), 4)
                for column, name in enumerate(_PROB_COLUMNS)
            }
        else:
            epoch.pop("probabilities", None)

    if artifact_intervals and settings["mark_artifacts"]:
        container = next(
            (c for c in ui.AnnotationContainer if c.label == settings["artifact_marker"]),
            None,
        )
        if container is not None:
            add_events_to_container(ui, artifact_intervals, container)

    return len(artifact_intervals)
