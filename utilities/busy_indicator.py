import threading
import traceback

from PySide6.QtCore import QEvent, QObject, Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

_BLOCKED_EVENTS = {
    QEvent.KeyPress, QEvent.KeyRelease, QEvent.Shortcut, QEvent.ShortcutOverride,
    QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick,
    QEvent.MouseMove, QEvent.Wheel, QEvent.ContextMenu,
}


class BusyIndicator(QWidget):
    """Semi-transparent layer with centered status text covering a window.

    While shown it swallows all mouse/keyboard/shortcut events application-wide.
    The GUI event loop keeps running, so the window keeps repainting.
    """

    def __init__(self, window, text):
        super().__init__(window)
        self._window = window
        self._text = text
        self.setGeometry(window.rect())
        self.show()
        self.raise_()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.instance().installEventFilter(self)

    def close_indicator(self):
        QApplication.instance().removeEventFilter(self)
        QApplication.restoreOverrideCursor()
        self.hide()
        self.deleteLater()

    def eventFilter(self, obj, event):
        if obj is self._window and event.type() == QEvent.Resize:
            self.setGeometry(self._window.rect())
        return event.type() in _BLOCKED_EVENTS

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 140))
        font = QFont(self.font())
        font.setPointSize(20)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(self.rect(), Qt.AlignCenter, self._text)


class _Runner(QObject):
    finished = Signal(object, object)  # result, exception

    def __init__(self, handler):
        super().__init__()
        self._handler = handler
        # bound QObject slot -> delivered on the GUI thread (this object's thread)
        self.finished.connect(self._on_finished)

    @Slot(object, object)
    def _on_finished(self, result, error):
        self._handler(result, error)


def run_busy(ui, text, work_fn, on_done, on_error=None):
    """Run work_fn() on a worker thread while a busy indicator covers the main window.

    work_fn must be pure compute (no GUI objects). on_done(result) then runs on the
    GUI thread. On failure on_error(exception) runs on the GUI thread (default: an
    error dialog). The indicator is removed in both cases.
    """
    window = ui.centralwidget.window()
    indicator = BusyIndicator(window, text)
    if not hasattr(ui, "_busy_runners"):
        ui._busy_runners = set()

    def finish(result, error):
        ui._busy_runners.discard(runner)
        indicator.close_indicator()
        if error is None:
            on_done(result)
        elif on_error is not None:
            on_error(error)
        else:
            QMessageBox.critical(window, "Error", str(error))

    runner = _Runner(finish)
    ui._busy_runners.add(runner)

    def target():
        try:
            result, error = work_fn(), None
        except Exception as e:
            traceback.print_exc()
            result, error = None, e
        runner.finished.emit(result, error)

    threading.Thread(target=target, daemon=True).start()
