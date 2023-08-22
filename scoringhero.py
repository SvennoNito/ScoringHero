# -*- coding: utf-8 -*-

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import scipy.io, os, sys, json, re, h5py, datetime
import numpy as np

from ui import * 
from data_handling import * 
from signal_processing import *
from utilities import *

class Ui_MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.devmode            = 1
        self.this_epoch         = 0
        self.default_data_path  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'example_data')
        
    def keyPressEvent(self, event):
        # print(event.key())
        if event.key() == Qt.Key_Right:
            next_epoch(self)  
        if event.key() == Qt.Key_Left:
            prev_epoch(self)  


    # *** Loading data ***
    @timing_decorator
    def load_eeg(self, datatype):
        self.eeg_data, self.config, self.stages, self.annotations, self.filename = load_eeg_wrapper(self.default_data_path, **{"datatype": datatype})
        self.times, self.numepo     = signal_times_vector(self.eeg_data.shape[1], self.config[0]['Sampling_rate_hz'], self.config[0]['Epoch_length_s'], self.config[0]['Extension_epoch_left_s'], self.config[0]['Extension_epoch_right_s'])
        self.toolbar_jump_to_epoch.setMaximum(self.numepo) 
        self.SignalWidget.draw_signal(self.config, self.eeg_data, self.times, self.this_epoch)
        self.DisplayedEpochWidget.update_text(self.this_epoch, self.numepo, self.stages)





if __name__ == "__main__":
    app         = QtWidgets.QApplication(sys.argv)
    MainWindow  = QtWidgets.QMainWindow()
    ui          = Ui_MainWindow()
    setup_ui(ui, MainWindow)
    if ui.devmode == 1:
        ui.eeg_data, ui.config, ui.stages, ui.annotations, ui.filename = load_all_important(f'{ui.default_data_path}\ST70MS_session3_scoringfile', {"datatype": 'eeglab'})
        ui.times, ui.numepo = signal_times_vector(ui.eeg_data.shape[1], ui.config[0]['Sampling_rate_hz'], ui.config[0]['Epoch_length_s'], ui.config[0]['Extension_epoch_left_s'], ui.config[0]['Extension_epoch_right_s'])
        ui.toolbar_jump_to_epoch.setMaximum(ui.numepo) 
        ui.SignalWidget.draw_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)
        ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)

    MainWindow.activateWindow()  # Add this line to make the window active
    MainWindow.show()
    sys.exit(app.exec())
