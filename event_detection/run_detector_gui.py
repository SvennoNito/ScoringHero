import traceback

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog

from events.add_events_to_container import add_events_to_container
from event_detection.run_detector import DetectorUnavailable, run_detector
from scoring.write_scoring import write_scoring
from utilities.refresh_gui import refresh_gui


def run_event_detector(ui, spec, settings):
    """Run `spec` on the chosen channel with a progress dialog, add the events to the
    Event container named by `settings["marker"]`, save, redraw. Errors are shown in a
    dialog. Returns True on success."""
    progress = QProgressDialog(f"Running {spec.method}…", None, 0, 0)
    progress.setWindowTitle(spec.title)
    progress.setWindowModality(Qt.WindowModal)
    progress.setCancelButton(None)
    progress.setMinimumDuration(0)
    progress.show()
    progress.raise_()
    QApplication.processEvents()

    try:
        events_sec = run_detector(
            spec,
            settings,
            ui.eeg_data_display,
            [ch["Channel_name"] for ch in ui.config[1]],
            float(ui.config[0]["Sampling_rate_hz"]),
            ui.scoring,
        )
        container = next(c for c in ui.AnnotationContainer if c.label == settings["marker"])
        add_events_to_container(ui, events_sec, container)

        progress.setLabelText(f"Done — {len(events_sec)} {spec.noun}(s) detected.")
        QApplication.processEvents()

        write_scoring(ui)
        ui.HypnogramWidget.draw_hypnogram(ui)
        refresh_gui(ui)

        QTimer.singleShot(1500, progress.close)
        return True

    except DetectorUnavailable as exc:
        progress.close()
        QMessageBox.critical(None, exc.title, exc.message)
    except Exception as exc:
        progress.close()
        QMessageBox.critical(
            None,
            f"{spec.method} Error",
            f"An error occurred during {spec.method} detection:\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            f"{traceback.format_exc()}",
        )
    return False
