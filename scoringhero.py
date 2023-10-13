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
        self.setWindowTitle("Scoring Hero")
        self.ui = ui

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
        self.version = 'v0.0'
        self.devmode = 0
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

    # *** Loading data ***
    @timing_decorator
    def load_eeg(self, datatype):
        eeg_import_window(self, datatype)
        times_vector(self)
        self.toolbar_jump_to_epoch.setMaximum(self.numepo)
        self.SignalWidget.draw_signal(self.config, self.eeg_data, self.times, self.this_epoch)
        self.DisplayedEpochWidget.update_text(self.this_epoch, self.numepo, self.stages)
        load_cache(self)
        self.SpectogramWidget.draw_spectogram(self.power, self.freqs, self.freqsOI, self.config)
        self.HypnogramWidget.draw_hypnogram(self.stages, self.numepo, self.config, self.swa)
        for container in self.AnnotationContainer:
            draw_event_in_this_epoch(self, container)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = Ui_MainWindow()
    MainWindow = MyMainWindow(ui)
    setup_ui(ui, MainWindow)
    if ui.devmode == 1:
        ui.filename = f"{ui.default_data_path}\example_data"
        load_wrapper(ui, datatype="eeglab")
        times_vector(ui)
        ui.toolbar_jump_to_epoch.setMaximum(ui.numepo)
        ui.SignalWidget.draw_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)
        ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)
        load_cache(ui)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)
        ui.HypnogramWidget.draw_hypnogram(ui.stages, ui.numepo, ui.config, ui.swa)
        for container in ui.AnnotationContainer:
            draw_event_in_this_epoch(ui, container)

    MainWindow.activateWindow()  # Add this line to make the window active
    MainWindow.show()
    sys.exit(app.exec())
