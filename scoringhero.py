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
            self.this_epoch = next_epoch(self.this_epoch, self.numepo)  
            self.SignalWidget.update_signal(self.config, self.eeg_data, self.times, self.this_epoch)
        if event.key() == Qt.Key_Left:
            self.this_epoch = prev_epoch(self.this_epoch)  
            self.SignalWidget.update_signal(self.config, self.eeg_data, self.times, self.this_epoch)


    # *** Loading data ***
    def load_eeg(self, datatype):
        self.eeg_data, self.config = load_eeg_wrapper(self.default_data_path, **{"datatype": datatype})
        self.times, self.numepo = signal_times_vector(self.eeg_data.shape[1], self.config[0]['Sampling_rate_hz'], self.config[0]['Epoch_length_s'], self.config[0]['Extension_epoch_left_s'], self.config[0]['Extension_epoch_right_s'])
        #self.BackgroundWidget.draw_background(self.eeg_data, self.times, self.this_epoch)
        self.SignalWidget.draw_signal(self.config, self.eeg_data, self.times, self.this_epoch)





if __name__ == "__main__":
    app         = QtWidgets.QApplication(sys.argv)
    MainWindow  = QtWidgets.QMainWindow()
    ui          = Ui_MainWindow()
    setup_ui(ui, MainWindow)
    if ui.devmode == 1:
        ui.eeg_data = load_mat_eeglab(f'{ui.default_data_path}\ST70MS_session3_scoringfile')
        ui.config = load_configuration(f'{ui.default_data_path}\ST70MS_session3_scoringfile.config.json', ui.eeg_data.shape[0])
        ui.times, ui.numepo = signal_times_vector(ui.eeg_data.shape[1], ui.config[0]['Sampling_rate_hz'], ui.config[0]['Epoch_length_s'], ui.config[0]['Extension_epoch_left_s'], ui.config[0]['Extension_epoch_right_s'])
        ui.SignalWidget.draw_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)

    MainWindow.activateWindow()  # Add this line to make the window active
    MainWindow.show()
    sys.exit(app.exec())
