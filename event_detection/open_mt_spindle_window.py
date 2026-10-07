from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from widgets import MtSpindleWindow
from scoring_model.events import N_SLOTS
from event_detection.mt_spindle import detect_spindle
from event_detection.run_detector import DetectorSpec
from event_detection.run_detector_gui import run_event_detector

SPEC = DetectorSpec(
    detect=detect_spindle,
    args=lambda s: dict(
        fmin=s["fmin"],
        fmax=s["fmax"],
        amin=s["amin"],
        dmin_s=s["dmin_s"],
        dmax_s=s["dmax_s"],
        q=s["q"],
    ),
    method="MT-Spindle",
    title="Spindle Detection (MT-Spindle)",
    noun="spindle",
)


def open_mt_spindle_window(ui):
    if not hasattr(ui, "eeg_data_display") or ui.eeg_data_display is None:
        QMessageBox.warning(None, "No data loaded", "Please load EEG data first.")
        return

    channel_labels    = [ch["Channel_name"] for ch in ui.config[1]]
    annotation_labels = [ui.events.label(slot) for slot in range(N_SLOTS)]
    has_stages        = any(stage is not None for stage in ui.scoring.stages())

    ui.MtSpindleWindow = MtSpindleWindow(channel_labels, annotation_labels, has_stages)
    ui.MtSpindleWindow.settingsAccepted.connect(
        lambda settings: QTimer.singleShot(0, lambda: run_event_detector(ui, SPEC, settings))
    )
    ui.MtSpindleWindow.show()
