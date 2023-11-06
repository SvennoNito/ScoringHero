# -*- coding: utf-8 -*-

# To do
# Automatic scoring
# Ability to overlay two scorings
# Read different scoring formats
# Read EDF files

# Option to randomize files
# Hypnogram on top of spectogram
# Scoring should save channels on which it was scored
# Start import where last import stopped


from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import scipy.io, os, sys, json, re, h5py, datetime
import numpy as np

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


class MyMainWindow(QtWidgets.QMainWindow):
    def __init__(self, ui):
        super().__init__()        
        self.setObjectName("ScoringHero")
        self.resize(800, 600)
        self.setStyleSheet("background-color: white;")
        self.ui = ui
        self.ui.version = [0, 0, 1]      
        self.setWindowTitle(f"Scoring Hero v.{self.ui.version[0]}.{self.ui.version[1]}.{self.ui.version[2]}")

    def closeEvent(self, event):
        if None in [stage["stage"] for stage in self.ui.stages]:
            messagebox = QMessageBox()
            messagebox.setIcon(QMessageBox.Warning)
            messagebox.setWindowTitle("Scoring incomplete")
            messagebox.setText(
                "There are unscored epochs.\nAre you sure you want to exit Scoring Hero?"
            )
            messagebox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            messagebox.setDefaultButton(QMessageBox.Cancel)

            response = messagebox.exec_()
            if response == QMessageBox.Cancel:
                event.ignore()
                return
            else:
                write_scoring(ui)
                event.accept()


class Ui_MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.devmode = 1
        self.this_epoch = 0
        self.default_data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "example_data"
        )

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
        name_of_eegfile = f"{ui.default_data_path}\example_data.mat"
        ui.filename, suffix = os.path.splitext(name_of_eegfile)
        MainWindow.setWindowTitle(f"Scoring Hero v.{ui.version[0]}.{ui.version[1]}.{ui.version[2]} ({os.path.basename(name_of_eegfile)})")
        load_wrapper(ui, 'eeglab')

    MainWindow.activateWindow()  # Add this line to make the window active
    MainWindow.show()
    sys.exit(app.exec())
