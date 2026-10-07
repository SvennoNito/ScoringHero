# -*- coding: utf-8 -*-

# To do
# - also show the .json file scoringhero writes into
# add export tab to eport sleep scoring in different formats
# ability to overlay two scorings


from PySide6 import QtWidgets
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import os, sys
from importlib.metadata import version as _pkg_version

from utilities.welcome_banner import print_welcome_banner
from ui.setup_ui import setup_ui
from utilities.next_epoch import next_epoch
from utilities.prev_epoch import prev_epoch
from eeg.load_wrapper import load_wrapper
from widgets import *
from paint_event.rectangle_events import event_hotkey, erase_events_in_rectangles
from scoring.write_scoring import write_scoring
from scoring_model.clean_sync import sync_clean
from scoring_model.events import Events
from style.appstyler import appstyler
from style.apply_app_theme import apply_app_theme
from style.theme import app_icon_path
from PySide6.QtGui import QIcon

_EVENT_KEY_MAP = {
    Qt.Key_A: 0,
    Qt.Key_F1: 1,
    Qt.Key_F2: 2,
    Qt.Key_F3: 3,
    Qt.Key_F4: 4,
    Qt.Key_F5: 5,
    Qt.Key_F6: 6,
    Qt.Key_F7: 7,
    Qt.Key_F8: 8,
    Qt.Key_F9: 9,
    Qt.Key_F10: 10,
    Qt.Key_F11: 11,
    Qt.Key_F12: 12,
}


class GlobalKeyFilter(QObject):
    """Application-level event filter for event-label and epoch-navigation keys.

    Installed on QApplication so it fires regardless of which widget has focus.
    pyqtgraph's GraphicsView accepts key events without propagating them, so
    a widget-level keyPressEvent on MyMainWindow would never be reached.
    """

    def __init__(self, ui, parent=None):
        super().__init__(parent)
        self._ui = ui

    def eventFilter(self, obj, event):
        event_type = event.type()

        if event_type == QEvent.Type.KeyPress and not event.isAutoRepeat():
            key = event.key()
            focused = QApplication.focusWidget()
            in_text = isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox))

            if not in_text:
                if key == Qt.Key_Right:
                    next_epoch(self._ui)
                    return True
                if key == Qt.Key_Left:
                    prev_epoch(self._ui)
                    return True
                if key == Qt.Key_Backspace:
                    erase_events_in_rectangles(self._ui)
                    return True
                if key in _EVENT_KEY_MAP:
                    self._ui.held_event_key = _EVENT_KEY_MAP[key]
                    return True

        elif event_type == QEvent.Type.KeyRelease and not event.isAutoRepeat():
            key = event.key()
            if key in _EVENT_KEY_MAP and self._ui.held_event_key is not None:
                slot = _EVENT_KEY_MAP[key]
                if self._ui.relabeled_event:
                    self._ui.relabeled_event = False
                else:
                    event_hotkey(slot, self._ui)
                self._ui.held_event_key = None
                return True

        return False


class MyMainWindow(QtWidgets.QMainWindow):
    def __init__(self, ui):
        super().__init__()
        self.setObjectName("ScoringHero")
        self.resize(800, 600)
        self.ui = ui
        self.ui.version = [int(x) for x in _pkg_version("scoringhero").split(".")]
        self.setWindowTitle(f"Scoring Hero v.{self.ui.version[0]}.{self.ui.version[1]}.{self.ui.version[2]}")

    def closeEvent(self, event):
        if self.ui.scoring is None:
            return  # no recording opened
        stages = self.ui.scoring.stages()
        n_unscored_epochs = sum(1 for stage in stages if stage is None)
        if n_unscored_epochs == 1:
            text_plural = ["is", "epoch"]
        else:
            text_plural = ["are", "epochs"]

        if n_unscored_epochs / len(stages) < .5 and n_unscored_epochs != 0:
            # Raise warning message when 50% or less epochs were not scored. 
            # If the message always pops up it the user habituates to the message unintentionally. 
            messagebox = QMessageBox()
            messagebox.setIcon(QMessageBox.Warning)
            messagebox.setWindowTitle("Scoring incomplete")
            messagebox.setText(
                f"There {text_plural[0]} <b>{n_unscored_epochs} unscored {text_plural[1]}</b>. You can click <i>Next unscored</i> in the navigation bar to jump to the respective {text_plural[1]}. Are you sure you want to exit Scoring Hero?"
            )
            messagebox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            messagebox.setDefaultButton(QMessageBox.Cancel)

            response = messagebox.exec()
            if response == QMessageBox.Cancel:
                event.ignore()
                return
            else:
                self.ui.save_scoring()
                event.accept()


class Ui_MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.devmode = 0
        self.this_epoch = 0
        self.held_event_key = None
        self.relabeled_event = False
        self.scoring = None
        self.events = Events(30, 0)  # 13 slots from startup; the grid follows the recording
        self.scoring_comparison = None
        self.comparison_name = None
        self.comparison_suffix = ""
        self.scoring_save_failed = False

        self.eeg_data_ref = None
        self.eeg_data_display_ref = None
        self.show_overlay = False
        self.analysis_source = "original"

        # Default paths
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller: resources in temp extraction dir, exe is the real location
            self.app_path = sys._MEIPASS
            self.default_data_path = os.path.dirname(os.path.abspath(sys.executable))
        elif os.environ.get('NUITKA_ONEFILE_PARENT'):
            # Nuitka onefile: __file__ is the temp extraction dir (where resources are)
            # sys.executable is the actual .exe path
            self.app_path = os.path.dirname(os.path.abspath(__file__))
            self.default_data_path = os.path.dirname(os.path.abspath(sys.executable))
        else:
            # Running as a script
            self.app_path = os.path.dirname(os.path.abspath(__file__))
            self.default_data_path = os.path.join(self.app_path, "example_data")

    def edit_events(self, edit):
        """The GUI step after every event edit. `edit` is called with Events and does the
        edit; then the Scoring clean flags follow slot 0 if it changed, the event boxes and
        the hypnogram event markers are redrawn and the scoring file is written. Returns
        what `edit` returns."""
        before = self.events.artefact_epochs()
        result = edit(self.events)
        after = self.events.artefact_epochs()
        if after != before:
            sync_clean(self.scoring, before, after)
        self.SignalWidget.draw_events(self.events, self.this_epoch)
        self.HypnogramWidget.update_events(self)
        self.save_scoring()
        return result

    def save_scoring(self):
        """Write the scoring file; a failure is reported in a message box and in the status bar."""
        path = f"{self.filename}.json"
        try:
            write_scoring(self.scoring, self.events, path)
            self.scoring_save_failed = False
        except Exception as e:
            self.scoring_save_failed = True
            error_message = f"An error occurred while writing the scoring file in \n{path}: \n\n{str(e)} \n\nThis means that the latest change in the scoring file was not saved! Please 1) screenshot this errorbox and 2) go to the black command window that opened with this program and copy the last error messages. Please report this bug so that it can be fixed fast!"
            QMessageBox.critical(self, "Error", error_message)
        self.StatusReadout.update(self)

    def keyPressEvent(self, event):
        # print(event.key())
        if event.key() == Qt.Key_Right:
            next_epoch(self)
        if event.key() == Qt.Key_Left:
            prev_epoch(self)


if __name__ == "__main__":
    print_welcome_banner()
    if sys.platform == "win32":
        # Own taskbar identity, so Windows shows our icon instead of grouping under python.exe
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ScoringHero.ScoringHero")
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QIcon(app_icon_path()))

    ui = Ui_MainWindow()
    MainWindow = MyMainWindow(ui)

    key_filter = GlobalKeyFilter(ui, app)
    app.installEventFilter(key_filter)

    setup_ui(ui, MainWindow)
    if ui.devmode == 1:
        name_of_eegfile = os.path.join(ui.default_data_path, "example_data.mat")
        ui.filename, suffix = os.path.splitext(name_of_eegfile)
        ui.eeg_file_name = os.path.basename(name_of_eegfile)
        ui.eeg_extra_files = 0
        load_wrapper(ui, 'eeglab')

    appstyler(app)
    apply_app_theme(MainWindow, app, ui.app_path, "modern_theme.qss")

    MainWindow.activateWindow()  # Add this line to make the window active
    MainWindow.show()
    sys.exit(app.exec())
