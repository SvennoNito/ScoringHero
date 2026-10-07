from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from widgets import SumoWindow
from event_detection.sumo_runner import detect_spindles
from event_detection.run_detector import DetectorSpec
from event_detection.run_detector_gui import run_event_detector

SPEC = DetectorSpec(
    detect=detect_spindles,
    args=lambda s: dict(
        prob_threshold=s["prob_threshold"],
    ),
    method="SUMO",
    title="Spindle Detection (SUMO)",
    noun="spindle",
)


def open_sumo_window(ui):
    if not hasattr(ui, "eeg_data_display") or ui.eeg_data_display is None:
        QMessageBox.warning(None, "No data loaded", "Please load EEG data first.")
        return

    channel_labels    = [ch["Channel_name"] for ch in ui.config[1]]
    slot_labels = ui.events.labels()
    has_stages        = any(stage is not None for stage in ui.scoring.stages())

    ui.SumoWindow = SumoWindow(channel_labels, slot_labels, has_stages)
    ui.SumoWindow.settingsAccepted.connect(
        lambda settings: QTimer.singleShot(0, lambda: run_event_detector(ui, SPEC, settings))
    )
    ui.SumoWindow.show()
