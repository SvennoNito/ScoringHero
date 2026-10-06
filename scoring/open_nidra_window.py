"""
open_nidra_window.py — GUI flow for automatic sleep staging with NIDRA.

NIDRA (Zerr 2025, https://github.com/paulzerr/nidra) bundles the ezscore-f
models (Coon et al. 2025) for two-channel forehead EEG as ONNX files. The
models run with onnxruntime inside ScoringHero — see nidra_runner.py. This
module collects the settings, applies the result to ui.stages and reports
progress.
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

from widgets import NidraWindow, NidraSummaryWindow
from events.add_events_to_container import add_events_to_container
from utilities.refresh_gui import refresh_gui
from .nidra_env import (
    MODELS,
    INSTALL_INSTRUCTIONS,
    default_model_root,
    find_model_file,
    download_model_file,
    missing_requirements,
    is_frozen,
)
from .write_scoring import write_scoring

_SETTINGS_FILE = "nidra_settings.json"

# NIDRA hypnogram codes -> ScoringHero (stage, digit). 4 is unused (where AASM
# once had N4); 6 = artifact, handled apart.
_STAGE_MAP = {
    0: ("Wake",  1),
    1: ("N1",   -1),
    2: ("N2",   -2),
    3: ("N3",   -3),
    5: ("REM",   0),
}

_ARTIFACT_CODE = 6


# --------------------------------------------------------------------------
# Persisted settings
# --------------------------------------------------------------------------

def _settings_paths(ui):
    """Where the NIDRA settings live, most preferred first.

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
    for path in _settings_paths(ui):
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as handle:
                return json.load(handle)
        except Exception:
            continue
    return {}


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

def open_nidra_window(ui):
    if not hasattr(ui, "eeg_data_display") or ui.eeg_data_display is None:
        QMessageBox.warning(None, "No data loaded", "Please load EEG data first.")
        return

    missing = missing_requirements()
    if missing:
        QMessageBox.information(
            None,
            "NIDRA requirements missing",
            f"NIDRA scoring needs {', '.join(missing)}, which cannot be imported "
            "in this interpreter.\n\n" + INSTALL_INSTRUCTIONS,
        )
        return

    # Keep the name->index cache in step with the current channel config, so
    # _channel_index() below cannot fail on a channel the dialog offers.
    from utilities.channel_index import rebuild_channel_index
    rebuild_channel_index(ui)

    channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
    annotation_labels = [container.label for container in ui.AnnotationContainer]

    ui.NidraWindow = NidraWindow(
        channel_labels,
        annotation_labels,
        saved=_load_settings(ui),
    )
    ui.NidraWindow.settingsAccepted.connect(
        lambda settings: _after_nidra_settings(ui, settings)
    )
    ui.NidraWindow.show()


def _after_nidra_settings(ui, settings):
    _save_settings(ui, settings)

    model_key = settings["model"]

    # Step A: epoch length
    epolen = ui.config[0]["Epoch_length_s"]
    if epolen != 30:
        message = QMessageBox()
        message.setIcon(QMessageBox.Warning)
        message.setWindowTitle("Epoch length mismatch")
        message.setText(
            f"The NIDRA models use 30-second epochs, but your epoch length is "
            f"{epolen}s.\n\nThe scores will be mapped onto your epoch grid "
            "automatically.\n\nYou can adjust the epoch length in the "
            "Configuration panel if you prefer 30s epochs."
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
    model_path = _ensure_model(settings, model_key)
    if model_path is None:
        return

    # Step D: run
    progress = QProgressDialog(f"Starting {model_key}...", "Cancel", 0, 0)
    progress.setWindowTitle("Auto Score (NIDRA)")
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)
    progress.setAutoClose(False)
    progress.setAutoReset(False)
    progress.show()
    progress.raise_()
    QApplication.processEvents()

    QTimer.singleShot(
        0,
        lambda: _execute_nidra(ui, settings, model_path, mode, overwrite_stages, progress),
    )


# --------------------------------------------------------------------------
# Model weights
# --------------------------------------------------------------------------

def _ensure_model(settings, model_key):
    """Return the path of the model's .onnx file, downloading it if the user agrees."""
    filename = MODELS[model_key]["files"]["default"]
    extra_root = settings.get("model_dir", "").strip()

    found = find_model_file(filename, extra_root)
    if found:
        return found

    target_dir = extra_root or default_model_root()
    answer = QMessageBox.question(
        None,
        "Download NIDRA model",
        f"The model file '{filename}' was not found.\n\n"
        f"Download it now from NIDRA's model repository to:\n{target_dir}",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes,
    )
    if answer != QMessageBox.Yes:
        return None

    progress = QProgressDialog(f"Downloading '{filename}'...", "Cancel", 0, 100)
    progress.setWindowTitle("Download NIDRA model")
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)
    progress.setAutoClose(False)
    progress.setAutoReset(False)
    progress.show()
    QApplication.processEvents()

    def on_progress(done, total):
        megabytes = done / (1 << 20)
        if total:
            progress.setValue(int(100 * done / total))
            progress.setLabelText(
                f"Downloading '{filename}' — {megabytes:.1f} of "
                f"{total / (1 << 20):.1f} MB"
            )
        else:
            progress.setLabelText(f"Downloading '{filename}' — {megabytes:.1f} MB")
        QApplication.processEvents()
        return not progress.wasCanceled()

    try:
        path = download_model_file(filename, target_dir, progress_cb=on_progress)
    except Exception as exc:
        progress.close()
        if progress.wasCanceled():
            return None
        QMessageBox.critical(
            None,
            "Download failed",
            f"The NIDRA model could not be downloaded:\n\n{type(exc).__name__}: {exc}\n\n"
            "You can also download it by hand from\n"
            "https://huggingface.co/pzerr/NIDRA_models\n"
            f"and place it in:\n{target_dir}",
        )
        return None

    progress.close()
    return path


# --------------------------------------------------------------------------
# Inference
# --------------------------------------------------------------------------

def _channel_index(ui, name):
    index = ui.channel_name_to_idx.get(name)
    if index is None:
        raise ValueError(f"Unknown channel: {name}")
    return index


def _execute_nidra(ui, settings, model_path, mode, overwrite_stages, progress):
    from .nidra_runner import (
        FOREHEAD_CLASSES,
        NidraCancelled,
        render_summary_figure,
        run_forehead,
    )

    summary_png = None
    try:
        sfreq = float(ui.config[0]["Sampling_rate_hz"])
        model_key = settings["model"]

        def tick(message):
            progress.setLabelText(message)
            QApplication.processEvents()
            return not progress.wasCanceled()

        left_name = settings["left_channel"]
        left_index = _channel_index(ui, left_name)
        if settings["duplicate_left"]:
            right_index = left_index
            channels_used = [left_name]
        else:
            right_name = settings["right_channel"]
            right_index = _channel_index(ui, right_name)
            channels_used = [left_name, right_name]

        data_volts = np.vstack([
            ui.eeg_data_display[left_index],
            ui.eeg_data_display[right_index],
        ]).astype(np.float64) / 1e6

        hypnogram, probabilities = run_forehead(
            data_volts, sfreq, model_path, tick=tick
        )
        class_names = FOREHEAD_CLASSES

        n_artifact = _apply_scores(
            ui, settings, hypnogram, probabilities, class_names,
            channels_used, mode, overwrite_stages,
        )

        progress.setLabelText(f"Finished — {len(hypnogram)} epochs scored.")
        QApplication.processEvents()

        write_scoring(ui)
        ui.HypnogramWidget.draw_hypnogram(ui)
        refresh_gui(ui)

        if settings["show_summary"]:
            handle = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            handle.close()
            summary_png = handle.name
            try:
                render_summary_figure(
                    hypnogram, probabilities, class_names, summary_png, title=model_key
                )
            except Exception as exc:  # a failed figure must not lose the scoring
                print(f"NIDRA: could not render the summary figure: {exc}")
                summary_png = None

        QTimer.singleShot(1200, progress.close)

        if summary_png and os.path.isfile(summary_png):
            ui.NidraSummaryWindow = NidraSummaryWindow(summary_png)
            ui.NidraSummaryWindow.show()
            summary_png = None  # the window keeps reading the file

        if n_artifact:
            QTimer.singleShot(
                1300,
                lambda: QMessageBox.information(
                    None,
                    "NIDRA finished",
                    f"{n_artifact} of {len(hypnogram)} epoch(s) were classified as "
                    "artifact and handled according to your artifact setting.",
                ),
            )

    except NidraCancelled:
        progress.close()

    except Exception as exc:
        import traceback
        traceback_text = traceback.format_exc()
        progress.close()
        QMessageBox.critical(
            None,
            "NIDRA Error",
            f"An error occurred while running NIDRA:\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            f"Traceback:\n{traceback_text}",
        )

    finally:
        if summary_png and os.path.isfile(summary_png):
            try:
                os.unlink(summary_png)
            except OSError:
                pass


def _apply_scores(
    ui, settings, hypnogram, probabilities, class_names,
    channels_used, mode, overwrite_stages,
):
    """Write the NIDRA result into ui.stages. Returns the artifact epoch count."""
    from .nidra_runner import CODE_TO_COLUMN

    epolen = ui.config[0]["Epoch_length_s"]
    source = f"NIDRA ({settings['model']})"
    artifact_mode = settings["artifact_mode"]
    store_probabilities = settings["store_probabilities"]

    artifact_intervals = []

    for index, epoch in enumerate(ui.stages):
        if mode == "fill_missing" and epoch["stage"] is not None:
            continue
        if mode == "selective" and epoch["stage"] not in overwrite_stages:
            continue

        if epolen == 30:
            nidra_index = index
        else:
            midpoint = (epoch["start"] + epoch["end"]) / 2.0
            nidra_index = int(midpoint // 30)

        if nidra_index < 0 or nidra_index >= len(hypnogram):
            continue

        code = int(hypnogram[nidra_index])
        column = CODE_TO_COLUMN.get(code)
        confidence = (
            round(float(probabilities[nidra_index, column]), 4)
            if column is not None and column < probabilities.shape[1]
            else None
        )

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
                name: round(float(probabilities[nidra_index, position]), 4)
                for position, name in enumerate(class_names)
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
