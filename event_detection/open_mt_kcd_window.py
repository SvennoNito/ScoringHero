from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from widgets import MtKcdWindow
from event_detection.mt_kcd import detect_kc
from event_detection.run_detector import DetectorSpec
from event_detection.run_detector_gui import run_event_detector

SPEC = DetectorSpec(
    detect=detect_kc,
    args=lambda s: dict(amin=s["amin"], dmax_s=s["dmax_s"], q=s["q"], fmax=s["fmax"]),
    method="MT-KCD",
    title="K-Complex Detection (MT-KCD)",
    noun="KC",
)


def open_mt_kcd_window(ui):
    if not hasattr(ui, "eeg_data_display") or ui.eeg_data_display is None:
        QMessageBox.warning(None, "No data loaded", "Please load EEG data first.")
        return

    channel_labels    = [ch["Channel_name"] for ch in ui.config[1]]
    slot_labels = ui.events.labels()
    has_stages        = any(stage is not None for stage in ui.scoring.stages())

    ui.MtKcdWindow = MtKcdWindow(channel_labels, slot_labels, has_stages)
    ui.MtKcdWindow.settingsAccepted.connect(
        lambda settings: QTimer.singleShot(0, lambda: run_event_detector(ui, SPEC, settings))
    )
    ui.MtKcdWindow.show()
