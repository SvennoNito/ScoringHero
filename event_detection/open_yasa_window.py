from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from widgets import YasaWindow
from event_detection.yasa_runner import detect_spindles
from event_detection.run_detector import DetectorSpec
from event_detection.run_detector_gui import run_event_detector

SPEC = DetectorSpec(
    detect=detect_spindles,
    args=lambda s: dict(
        rel_pow=s["rel_pow"],
        corr=s["corr"],
        rms=s["rms"],
        min_dur=s["min_dur"],
        max_dur=s["max_dur"],
        freq_sp=s["freq_sp"],
        freq_broad=s["freq_broad"],
    ),
    method="YASA",
    title="Spindle Detection (YASA)",
    noun="spindle",
)


def open_yasa_window(ui):
    if not hasattr(ui, "eeg_data_display") or ui.eeg_data_display is None:
        QMessageBox.warning(None, "No data loaded", "Please load EEG data first.")
        return

    channel_labels    = [ch["Channel_name"] for ch in ui.config[1]]
    annotation_labels = [c.label for c in ui.AnnotationContainer]
    has_stages        = any(stage is not None for stage in ui.scoring.stages())

    ui.YasaWindow = YasaWindow(channel_labels, annotation_labels, has_stages)
    ui.YasaWindow.settingsAccepted.connect(
        lambda settings: QTimer.singleShot(0, lambda: run_event_detector(ui, SPEC, settings))
    )
    ui.YasaWindow.show()
