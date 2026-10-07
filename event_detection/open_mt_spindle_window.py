import numpy as np
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PySide6.QtCore import Qt, QTimer

from widgets import MtSpindleWindow
from event_detection.mt_spindle import detect_spindle
from events.add_events_to_container import add_events_to_container
from scoring.write_scoring import write_scoring
from autoscoring.autoscore_results import events_in_stages
from utilities.refresh_gui import refresh_gui


def open_mt_spindle_window(ui):
    if not hasattr(ui, "eeg_data_display") or ui.eeg_data_display is None:
        QMessageBox.warning(None, "No data loaded", "Please load EEG data first.")
        return

    channel_labels    = [ch["Channel_name"] for ch in ui.config[1]]
    annotation_labels = [c.label for c in ui.AnnotationContainer]
    has_stages        = any(stage is not None for stage in ui.scoring.stages())

    ui.MtSpindleWindow = MtSpindleWindow(channel_labels, annotation_labels, has_stages)
    ui.MtSpindleWindow.settingsAccepted.connect(
        lambda settings: _after_settings(ui, settings)
    )
    ui.MtSpindleWindow.show()


def _after_settings(ui, settings):
    progress = QProgressDialog("Running MT-Spindle spindle detection…", None, 0, 0)
    progress.setWindowTitle("Spindle Detection (MT-Spindle)")
    progress.setWindowModality(Qt.WindowModal)
    progress.setCancelButton(None)
    progress.setMinimumDuration(0)
    progress.show()
    progress.raise_()
    QApplication.processEvents()
    QTimer.singleShot(0, lambda: _execute(ui, settings, progress))


def _execute(ui, settings, progress):
    try:
        ch_idx    = ui.channel_name_to_idx.get(settings["channel"], 0)
        sfreq     = float(ui.config[0]["Sampling_rate_hz"])
        signal_1d = ui.eeg_data_display[ch_idx].copy().astype(np.float64)

        events_sec = detect_spindle(
            signal_1d,
            sfreq,
            fmin=settings["fmin"],
            fmax=settings["fmax"],
            amin=settings["amin"],
            dmin_s=settings["dmin_s"],
            dmax_s=settings["dmax_s"],
            q=settings["q"],
        )

        # Stage filter
        filter_stages = settings.get("filter_stages")
        if filter_stages:
            events_sec = events_in_stages(ui.scoring, events_sec, filter_stages)

        marker_label = settings["marker"]
        container = next(c for c in ui.AnnotationContainer if c.label == marker_label)
        add_events_to_container(ui, events_sec, container)

        progress.setLabelText(f"Done — {len(events_sec)} spindle(s) detected.")
        QApplication.processEvents()

        write_scoring(ui)
        ui.HypnogramWidget.draw_hypnogram(ui)
        refresh_gui(ui)

        QTimer.singleShot(1500, progress.close)

    except Exception as exc:
        import traceback
        progress.close()
        QMessageBox.critical(
            None,
            "MT-Spindle Error",
            f"An error occurred during spindle detection:\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            f"{traceback.format_exc()}",
        )
