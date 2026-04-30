import numpy as np
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PySide6.QtCore import Qt, QTimer

from widgets import SumoWindow
from scoring.sumo_runner import detect_spindles
from events.add_events_to_container import add_events_to_container
from scoring.write_scoring import write_scoring
from utilities.refresh_gui import refresh_gui


def open_sumo_window(ui):
    if not hasattr(ui, "eeg_data_display") or ui.eeg_data_display is None:
        QMessageBox.warning(None, "No data loaded", "Please load EEG data first.")
        return

    channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
    annotation_labels = [c.label for c in ui.AnnotationContainer]
    has_stages = any(s["stage"] is not None for s in ui.stages)

    ui.SumoWindow = SumoWindow(channel_labels, annotation_labels, has_stages)
    ui.SumoWindow.settingsAccepted.connect(
        lambda settings: _after_settings(ui, settings)
    )
    ui.SumoWindow.show()


def _after_settings(ui, settings):
    progress = QProgressDialog("Running SUMO spindle detection…", None, 0, 0)
    progress.setWindowTitle("Spindle Detection (SUMO)")
    progress.setWindowModality(Qt.WindowModal)
    progress.setCancelButton(None)
    progress.setMinimumDuration(0)
    progress.show()
    progress.raise_()
    QApplication.processEvents()
    QTimer.singleShot(0, lambda: _execute(ui, settings, progress))


def _execute(ui, settings, progress):
    try:
        channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
        ch_idx = channel_labels.index(settings["channel"])
        sfreq = float(ui.config[0]["Sampling_rate_hz"])
        signal_1d = ui.eeg_data_display[ch_idx].copy().astype(np.float64)

        progress.setLabelText("Loading SUMO model…")
        QApplication.processEvents()

        events_sec = detect_spindles(
            signal_1d,
            sfreq,
            prob_threshold=settings["prob_threshold"],
        )

        # Stage filter
        filter_stages = settings.get("filter_stages")
        if filter_stages:
            epoch_len = float(ui.config[0]["Epoch_length_s"])
            events_sec = _filter_by_stages(events_sec, ui.stages, epoch_len, filter_stages)

        marker_label = settings["marker"]
        container = next(c for c in ui.AnnotationContainer if c.label == marker_label)
        add_events_to_container(ui, events_sec, container)

        progress.setLabelText(f"Done — {len(events_sec)} spindle(s) detected.")
        QApplication.processEvents()

        write_scoring(ui)
        ui.HypnogramWidget.draw_hypnogram(ui)
        refresh_gui(ui)

        QTimer.singleShot(1500, progress.close)

    except ImportError:
        progress.close()
        QMessageBox.critical(
            None,
            "PyTorch Not Found",
            f"SUMO requires PyTorch to be installed.\n\n"
            f"Install PyTorch using one of these commands:\n"
            f"  • uv pip install torch\n"
            f"  • uv sync --extra sumo\n"
            f"  • pip install torch\n\n"
            f"For platform-specific instructions, visit:\n"
            f"https://pytorch.org/get-started/locally/",
        )
    except RuntimeError as exc:
        progress.close()

        # Check if it's a model download error
        if "download" in str(exc).lower() or "model" in str(exc).lower():
            QMessageBox.critical(
                None,
                "SUMO Model Setup Required",
                f"{str(exc)}\n\n"
                f"Quick start:\n"
                f"1. Run: python setup_sumo.py\n"
                f"2. Follow the manual download instructions\n"
                f"3. Restart ScoringHero\n\n"
                f"Repository: https://github.com/dslaborg/sumo",
            )
        else:
            QMessageBox.critical(
                None,
                "SUMO Error",
                f"An error occurred during SUMO spindle detection:\n\n"
                f"{type(exc).__name__}: {exc}",
            )
    except Exception as exc:
        import traceback

        progress.close()
        QMessageBox.critical(
            None,
            "SUMO Error",
            f"An error occurred during SUMO spindle detection:\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            f"Debug info:\n{traceback.format_exc()}",
        )


def _filter_by_stages(events_sec, stages, epoch_len, filter_stages):
    """Keep only events whose midpoint falls in one of the selected stages."""
    selected = set(filter_stages)
    kept = []
    for start, end in events_sec:
        mid = (start + end) / 2.0
        epoch_idx = int(mid / epoch_len)
        if epoch_idx < len(stages) and stages[epoch_idx]["stage"] in selected:
            kept.append([start, end])
    return kept
