# -*- coding: utf-8 -*-

# To do
# - also show the .json file scoringhero writes into
# add export tab to eport sleep scoring in different formats
# ability to overlay two scorings


from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import scipy.io, os, sys, json, re, h5py, datetime
import numpy as np
from importlib.metadata import version as _pkg_version

from ui.setup_ui import setup_ui
from utilities.timing_decorator import timing_decorator
from utilities.next_epoch import next_epoch
from utilities.prev_epoch import prev_epoch
from eeg.load_wrapper import load_wrapper
from eeg.eeg_import_window import eeg_import_window
from widgets import *
from signal_processing.times_vector import times_vector
from events.draw_event_in_this_epoch import draw_event_in_this_epoch
from cache.load_cache import load_cache
from scoring.write_scoring import write_scoring
from style.appstyler import appstyler
from style.apply_app_theme import apply_app_theme

class MyMainWindow(QtWidgets.QMainWindow):
    def __init__(self, ui):
        super().__init__()        
        self.setObjectName("ScoringHero")
        self.resize(800, 600)
        self.setStyleSheet("background-color: white;")
        self.ui = ui
        self.ui.version = [int(x) for x in _pkg_version("scoringhero").split(".")]
        self.setWindowTitle(f"Scoring Hero v.{self.ui.version[0]}.{self.ui.version[1]}.{self.ui.version[2]}")

    def closeEvent(self, event):
        n_unscored_epochs = sum(1 for stage in self.ui.stages if stage["digit"] is None)
        if n_unscored_epochs == 1:
            text_plural = ["is", "epoch"]
        else:
            text_plural = ["are", "epochs"]

        # if None in [stage["digit"] for stage in self.ui.stages]:
        if n_unscored_epochs / len(self.ui.stages) < .5 and n_unscored_epochs != 0:
            # Raise warning message when 50% or less epochs were not scored. 
            # If the message always pops up it the user habituates to the message unintentionally. 
            messagebox = QMessageBox()
            messagebox.setIcon(QMessageBox.Warning)
            messagebox.setWindowTitle("Scoring incomplete")
            messagebox.setText(
                f"There {text_plural[0]} <b>{n_unscored_epochs} unscored {text_plural[1]}</b>. You can click [unscored] in the toolbar to jump to the respective {text_plural[1]}. Are you sure you want to exit Scoring Hero?"
            )
            messagebox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            messagebox.setDefaultButton(QMessageBox.Cancel)

            response = messagebox.exec()
            if response == QMessageBox.Cancel:
                event.ignore()
                return
            else:
                write_scoring(ui)
                event.accept()


class Ui_MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.devmode = 0
        self.this_epoch = 0

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

    def keyPressEvent(self, event):
        # print(event.key())
        if event.key() == Qt.Key_Right:
            next_epoch(self)
        if event.key() == Qt.Key_Left:
            prev_epoch(self)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    ui = Ui_MainWindow()
    MainWindow = MyMainWindow(ui)
    
    setup_ui(ui, MainWindow)
    if ui.devmode == 1:
        name_of_eegfile = os.path.join(ui.default_data_path, "example_data.mat")
        ui.filename, suffix = os.path.splitext(name_of_eegfile)
        MainWindow.setWindowTitle(f"Scoring Hero v.{ui.version[0]}.{ui.version[1]}.{ui.version[2]} ({os.path.basename(name_of_eegfile)})")
        load_wrapper(ui, 'eeglab')

        # Enable menus, toolbar, and sliders
        ui.menu_stages.setEnabled(True)
        ui.menu_labels.setEnabled(True)
        ui.menu_utils.setEnabled(True)
        ui.menu_config.setEnabled(True)
        ui.toolbar_jump_to_epoch.setEnabled(True)
        ui.tool_nextunscored.setEnabled(True)
        ui.tool_nextuncertain.setEnabled(True)
        ui.tool_nexttransition.setEnabled(True)
        ui.tool_nextevent.setEnabled(True)
        ui.tool_nexthuman.setEnabled(True)
        ui.HypnogramSlider.enable_slider()

    appstyler(app)
    apply_app_theme(MainWindow, app, ui.app_path, "modern_theme.qss")

    MainWindow.activateWindow()  # Add this line to make the window active
    MainWindow.show()
    sys.exit(app.exec())
