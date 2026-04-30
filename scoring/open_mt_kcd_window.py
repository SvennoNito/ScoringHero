import numpy as np
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PySide6.QtCore import Qt, QTimer

from widgets import MtKcdWindow
from scoring.mt_kcd import detect_kc
from events.add_events_to_container import add_events_to_container
from scoring.write_scoring import write_scoring
from utilities.refresh_gui import refresh_gui


def open_mt_kcd_window(ui):
    if not hasattr(ui, "eeg_data_display") or ui.eeg_data_display is None:
        QMessageBox.warning(None, "No data loaded", "Please load EEG data first.")
        return

    channel_labels    = [ch["Channel_name"] for ch in ui.config[1]]
    annotation_labels = [c.label for c in ui.AnnotationContainer]
    has_stages        = any(s["stage"] is not None for s in ui.stages)

    ui.MtKcdWindow = MtKcdWindow(channel_labels, annotation_labels, has_stages)
    ui.MtKcdWindow.settingsAccepted.connect(
        lambda settings: _after_settings(ui, settings)
    )
    ui.MtKcdWindow.show()


def _after_settings(ui, settings):
    progress = QProgressDialog("Running MT-KCD K-complex detection…", None, 0, 0)
    progress.setWindowTitle("K-Complex Detection (MT-KCD)")
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

        events_sec = detect_kc(
            signal_1d,
            sfreq,
            amin=settings["amin"],
            dmax_s=settings["dmax_s"],
            q=settings["q"],
            fmax=settings["fmax"],
        )

        # Stage filter
        filter_stages = settings.get("filter_stages")
        if filter_stages:
            epoch_len  = float(ui.config[0]["Epoch_length_s"])
            events_sec = _filter_by_stages(events_sec, ui.stages, epoch_len, filter_stages)

        marker_label = settings["marker"]
        container = next(c for c in ui.AnnotationContainer if c.label == marker_label)
        add_events_to_container(ui, events_sec, container)

        progress.setLabelText(f"Done — {len(events_sec)} KC(s) detected.")
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
            "MT-KCD Error",
            f"An error occurred during MT-KCD detection:\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            f"{traceback.format_exc()}",
        )


def _filter_by_stages(events_sec, stages, epoch_len, filter_stages):
    """Keep only events whose midpoint falls in one of the selected stages."""
    selected = set(filter_stages)
    kept = []
    for start, end in events_sec:
        mid       = (start + end) / 2.0
        epoch_idx = int(mid / epoch_len)
        if epoch_idx < len(stages) and stages[epoch_idx]["stage"] in selected:
            kept.append([start, end])
    return kept


