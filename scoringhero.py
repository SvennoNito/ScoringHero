# -*- coding: utf-8 -*-

# To do
# Assign a button to apply configuration
# Green box wegclick error when it's very high
# Signal border not necessarily even on top and bottom
# Option to randomize files
# When closing, error message that says how many epochs were not scored
# Hypnogram on top of spectogram
# artefact more transparent
# Scoring should save channels on which it was scored

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import scipy.io, os, sys, json, re, h5py, datetime
import numpy as np

from ui import *
from data_handling import *
from utilities.timing_decorator import timing_decorator
from utilities.next_epoch import next_epoch
from utilities.prev_epoch import prev_epoch
from data_handling.load_eeg import load_eeg_wrapper, load_eeg_config_scoring
from mouse_click import *
from widgets import *
from signal_processing.build_times_vector import build_times_vector
from annotations.draw_box_in_epoch import draw_box_in_epoch
from data_handling.cache import load_cache


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

    # *** Loading data ***
    @timing_decorator
    def load_eeg(self, datatype):
        load_eeg_wrapper(self, datatype)
        build_times_vector(self)
        self.toolbar_jump_to_epoch.setMaximum(self.numepo)
        self.SignalWidget.draw_signal(self.config, self.eeg_data, self.times, self.this_epoch)
        self.DisplayedEpochWidget.update_text(self.this_epoch, self.numepo, self.stages)
        load_cache(self)
        self.SpectogramWidget.draw_spectogram(self.power, self.freqs, self.freqsOI, self.config)
        self.HypnogramWidget.draw_hypnogram(self.stages, self.numepo, self.config, self.swa)
        for container in self.AnnotationContainer:
            draw_box_in_epoch(self, container)  

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    setup_ui(ui, MainWindow)
    if ui.devmode == 1:
        ui.filename = f"{ui.default_data_path}\example_data"
        load_eeg_config_scoring(ui, datatype="eeglab")
        build_times_vector(ui)
        ui.toolbar_jump_to_epoch.setMaximum(ui.numepo)
        ui.SignalWidget.draw_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)
        ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)
        # spectogram_to_ui(ui)
        load_cache(ui)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)
        ui.HypnogramWidget.draw_hypnogram(ui.stages, ui.numepo, ui.config, ui.swa)
        for container in ui.AnnotationContainer:
            draw_box_in_epoch(ui, container)        

    MainWindow.activateWindow()  # Add this line to make the window active
    MainWindow.show()
    sys.exit(app.exec())
