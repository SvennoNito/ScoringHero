# -*- coding: utf-8 -*-

# *** to do ***
# 1) merge artifacts
# 2) click on artifact to disappear
# 3) "saved to" in toolbar
# 4) write configuration file and template
# 5) which includes the power spectrum range
# 6) and allows it to be on a log scale or not
# 7) option to save power spectrum

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import scipy.io, os, sys, json, re, h5py, datetime
import tkinter as tk 
import numpy as np
sys.path.append("ui_classes")
sys.path.append("functions")
from EEG_class import *
from greenLine import *
from hypnogram import *
import load_and_save_functions
import popups, spectral

# This software protects itself by being executable only until a certain date in the future.
expiration_date = datetime.datetime(2023, 12, 31)   # Set the expiration date
current_date    = datetime.datetime.now()           # Get the current date

class Ui_MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.devmode                        = 1
        self.this_epoch                     = 1
        self.containers                     = []
        self.name_of_eeg_file_before_extension = []
        self.name_of_scoring_file           = []
        self.path_to_this_script            = os.path.dirname(os.path.abspath(__file__))
        self.default_path_to_eeg_data       = os.path.join(self.path_to_this_script, 'example_data')
        self.default_path_to_scoring_file   = os.path.join(self.path_to_this_script, 'example_data')

    def keyPressEvent(self, event):
        # Define key press events
        # print(event.key())
        if event.key() == Qt.Key_Right:
            self.nextEpoch()     
        if event.key() == Qt.Key_Left:
            self.previousEpoch()      
        if event.key() == Qt.Key_F1:            
            self.containerF1.include(self.greenLine, self.EEG)
            self.write_scoring_file_as_json()    
        if event.key() == Qt.Key_F2:            
            self.containerF2.include(self.greenLine, self.EEG)
            self.write_scoring_file_as_json()    
        if event.key() == Qt.Key_F3:            
            self.containerF3.include(self.greenLine, self.EEG)
            self.write_scoring_file_as_json()    
        if event.key() == Qt.Key_F4:            
            self.containerF4.include(self.greenLine, self.EEG)
            self.write_scoring_file_as_json()    


    # *** Functions for loading EEG file ***
    def select_eeg_from_menu(self):
        name_of_eegfile, _      = QtWidgets.QFileDialog.getOpenFileName(None, 'Open File', self.default_path_to_eeg_data, '*.mat;*json')
        self.load_eeg_data_and_configuration_and_sleep_scoring(name_of_eegfile)    

    def select_random_eeg_from_menu(self):
        name_of_eegfiles, _     = QtWidgets.QFileDialog.getOpenFileNames(None, 'Select multiple EEG files', self.default_path_to_eeg_data, 'Matlab files (*.mat)')
        name_of_eegfile         = load_and_save_functions.choose_random_file_from_selection(name_of_eegfiles)
        self.load_eeg_data_and_configuration_and_sleep_scoring(name_of_eegfile)    

    def load_eeg_data_and_configuration_and_sleep_scoring(self, name_of_eegfile):
        self.name_of_eeg_file_before_extension, _   = os.path.splitext(name_of_eegfile)
        self.name_of_scoring_file                   = self.name_of_eeg_file_before_extension + '.json'
        self.default_path_to_eeg_data               = os.path.dirname(self.name_of_scoring_file)
        load_and_save_functions.load_eeg_and_configuration_settings(name_of_eegfile, self)
        self.initiate_GUI()
        load_and_save_functions.load_scoring_file(self.name_of_scoring_file, self.hypnogram, self.containers, self.spectogram.axes, self.EEG)
        self.refresh_GUI()


    # *** Functions for handling scoring file ***
    def write_scoring_file_as_json(self): 
        load_and_save_functions.write_scoring_file(self.name_of_scoring_file, self.EEG.epolen, self.hypnogram, self.containerA, self.containers)
                                               
    def load_scorin_file_from_menu(self):
        name_of_scoringfile, _                  = QtWidgets.QFileDialog.getOpenFileName(None, 'Open .json file', self.default_path_to_scoring_file, 'Json Files (*.json)')
        self.name_of_scoring_file               = name_of_scoringfile
        self.ndefault_path_to_scoring_file      = os.path.dirname(name_of_scoringfile)
        load_and_save_functions.load_scoring_file(name_of_scoringfile, self.hypnogram, self.containers, self.spectogram.axes, self.EEG)
        self.refresh_GUI()


    # *** Function tto set-up and regresh the GUI ***
    def initiate_GUI(self):
        self.hypnogram.initiate(self.EEG)
        self.spectogram.initiate(self.EEG)
        self.powerbox.initiate(self.EEG)
        self.greenLine.initiate(self.EEG)
        
        self.containerA         = popups.container(self.EEG.epolen, facecolor=(255, 200, 200, 100), label="Artefacts")
        self.containerF1        = popups.container(self.EEG.epolen, facecolor=(100, 149, 237, 100), label="Annotation_F1")
        self.containerF2        = popups.container(self.EEG.epolen, facecolor=(152, 251, 152, 100), label="Annotation_F2")
        self.containerF3        = popups.container(self.EEG.epolen, facecolor=(255, 255, 102, 100), label="Annotation_F3")
        self.containerF4        = popups.container(self.EEG.epolen, facecolor=(64, 224, 208, 100),  label="Annotation_F4")
        self.containers         = [self.containerA, self.containerF1, self.containerF2, self.containerF3, self.containerF4]
        for container in self.containers:
            container.changesMade.connect(self.remove_areas)         

        self.notes_editbox      = popups.editbox(self.containers)
        self.notes_editbox.changesMade.connect(self.edit_annotations)      
        #self.optionbox          = popups.options(self.EEG.return_extension())
        #self.optionbox.changesMade.connect(self.edit_displayed_eeg)     
        self.configuration_box   = popups.configuration_box(self.EEG.configuration)
        self.configuration_box.changesMade.connect(self.respond_to_configuration_pop_up) 
        self.configuration_box.finished.connect(self.respond_to_configuration_pop_up_closing)

        self.tool_epochjump.setRange(1, self.EEG.numepo)        
        self.EEG.changesMade.connect(self.show_artefacts) 

    def refresh_GUI(self):
        for container in self.containers:
            container.related_epoch()          
        this_stage, uncertainty = self.hypnogram.get_text(self.this_epoch)
        this_epoch = self.this_epoch
        self.EEG.update_text(this_epoch, this_stage, uncertainty)
        self.spectogram.add_line(this_epoch)
        #self.hypnogram.update(this_epoch)
        self.hypnogram.add_to_spectogram(this_epoch, self.spectogram.axes, self.containers)
        self.hypnogram.show_artefacts(self.containerA.epoch)
        self.powerbox.update(self.EEG.data[0][self.this_epoch-1])
        self.EEG.showEEG(self.this_epoch)
        self.resetGreenLine()        
       


    def options(self):
        self.optionbox.exec_()      

    def edit_displayed_eeg(self):
        self.EEG.edit_extension(self.this_epoch, self.optionbox)

    def edit_annotations(self):
        self.notes_editbox.exec_()
        for count, container in enumerate(self.containers):
            container.label = self.notes_editbox.labelbox[count].text()
            #palette = self.notes_editbox.labelbox[count].palette().color(QtGui.QPalette.Base)
            #annotation.facecolor = palette.red(), palette.green(), palette.blue(), 100  

    def remove_areas(self):
        1
        #for annotation in self.containers:
        #    annotation.remove_border(self.EEG)
                    
    def label_artefacts(self):
        #self.EEG.storeArtefacts(self.greenLine)  
        self.containerA.include(self.greenLine, self.EEG)
        self.hypnogram.show_artefacts(self.containerA.epoch)
        self.write_scoring_file_as_json()          

    def show_artefacts(self):
        for annotation in self.containers:
            annotation.show_areas(self.EEG)

    def saveSleepStages(self):
        self.name_of_scoring_file, _ = QFileDialog.getSaveFileName(None, "Save Sleep Stages", "", "Json Files (*.json)") # Open a file dialog to choose the save location and filename
        self.write_scoring_file_as_json()

    def resetGreenLine(self):
        if self.greenLine:
            self.greenLine.reset()       
        



   

    def scoreN1(self):     
        self.hypnogram.assign(self.this_epoch, self.hypnogram.N1, self.EEG.return_active_channels())
        self.refresh_GUI()   
        self.nextEpoch()
        self.write_scoring_file_as_json()

    def scoreN2(self):     
        self.hypnogram.assign(self.this_epoch, self.hypnogram.N2, self.EEG.return_active_channels())
        self.refresh_GUI() 
        self.nextEpoch()
        self.write_scoring_file_as_json()

    def scoreN3(self):     
        self.hypnogram.assign(self.this_epoch, self.hypnogram.N3, self.EEG.return_active_channels())
        self.refresh_GUI() 
        self.nextEpoch()
        self.write_scoring_file_as_json()

    def scoreWake(self):     
        self.hypnogram.assign(self.this_epoch, self.hypnogram.W, self.EEG.return_active_channels())
        self.refresh_GUI() 
        self.nextEpoch()
        self.write_scoring_file_as_json()

    def scoreREM(self):     
        self.hypnogram.assign(self.this_epoch, self.hypnogram.REM, self.EEG.return_active_channels())
        self.refresh_GUI()        
        self.nextEpoch() 
        self.write_scoring_file_as_json()    

    def scoring_uncertainty(self):
        self.hypnogram.express_uncertainty(self.this_epoch)
        self.refresh_GUI()   
        self.write_scoring_file_as_json()     

    def hypnoClick(self, event):
        self.this_epoch = self.hypnogram.onclick(event)
        self.EEG.showEEG(self.this_epoch)
        self.refresh_GUI()

    def spectogramClick(self, event):
        self.this_epoch = self.spectogram.map(event)
        self.EEG.showEEG(self.this_epoch)
        self.refresh_GUI()            

    def previousEpoch(self):
        if self.this_epoch > 1:
            self.this_epoch -= 1
            self.EEG.showEEG(self.this_epoch) # Plot previous epoch   
            self.refresh_GUI() 

    def nextEpoch(self):
        if self.this_epoch < self.EEG.numepo:
            self.this_epoch += 1       
            self.EEG.showEEG(self.this_epoch) # Plot next epoch
            self.refresh_GUI() 

    def scaleChannels(self):
        self.scaleDialogeBox = popups.scaleDialogeBox(self.EEG.chaninfo)
        self.scaleDialogeBox.changesMade.connect(self.respond_to_scaleDialogeBox)
        self.scaleDialogeBox.exec_()

    def respond_to_scaleDialogeBox(self):
        self.EEG.scaleChannels(self.scaleDialogeBox.chaninfo, self.this_epoch) 
        load_and_save_functions.update_channel_information_in_configuration_file(self.name_of_eeg_file_before_extension + '.config.json', self.scaleDialogeBox.chaninfo)

    def configuration_pop_up(self):
        self.configuration_box.exec()

    def respond_to_configuration_pop_up(self):
        self.EEG.add_info(self.configuration_box.configuration)
        self.EEG.update2()
        self.EEG.showEEG(self.this_epoch)  
        load_and_save_functions.update_general_information_in_configuration_file(self.name_of_eeg_file_before_extension + '.config.json', self.configuration_box.configuration)
        
    def respond_to_configuration_pop_up_closing(self):
        self.spectogram.change_configuration(self.configuration_box.configuration)
        self.spectogram.initiate(self.EEG)
        self.refresh_GUI()

    def jump_to_epoch(self):
        self.this_epoch = self.tool_epochjump.value()
        self.EEG.showEEG(self.this_epoch)
        self.refresh_GUI()

    def jump_to_unscored_epoch(self):
        self.this_epoch = self.hypnogram.get_next_unscored()
        self.EEG.showEEG(self.this_epoch)
        self.refresh_GUI()

    def jump_to_transition(self):
        self.this_epoch = self.hypnogram.get_next_transition(self.this_epoch)
        self.EEG.showEEG(self.this_epoch)
        self.refresh_GUI()        

    def jump_to_uncertain_epoch(self):
        self.this_epoch = self.hypnogram.get_next_uncertain()
        self.EEG.showEEG(self.this_epoch)
        self.refresh_GUI()            




       
            
      

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.showMaximized()

        # set the grid layout
        layout = QtWidgets.QGridLayout()
        self.centralwidget.setLayout(layout) 

        # Create classes
        self.EEG        = EEG_class(self.centralwidget)
        self.hypnogram  = hypnogram(self.centralwidget)
        self.spectogram = spectral.spectogram(self.centralwidget)
        self.powerbox   = spectral.powerbox(self.centralwidget)
        self.greenLine  = greenLine(self.powerbox)
        self.hypnogram.axes.scene().sigMouseClicked.connect(self.hypnoClick)
        self.spectogram.graphics.scene().sigMouseClicked.connect(self.spectogramClick)

        # Layout
        layout.addWidget(self.EEG.axes,                 10, 0,  85,  100)
        layout.addWidget(self.greenLine,                10, 0,  85,  100)     
        layout.addWidget(self.spectogram.graphics,      0,  0,  10,  85)
        #layout.addWidget(self.hypnogram.axes,           0, 85,  10,  15)
        layout.addWidget(self.powerbox.axes,           0, 85,  10,  15)
        #layout.addWidget(self.epochpower.axes,          95, 0,  5, 100)

   




        # Menubar
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")

        # File menu
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")    
        self.menubar.addAction(self.menuFile.menuAction())  

        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionOpen.triggered.connect(lambda: self.select_eeg_from_menu())
        self.menuFile.addAction(self.actionOpen)
        self.actionRandom = QtWidgets.QAction(MainWindow)
        self.actionRandom.setObjectName("actionRandom")
        self.actionRandom.triggered.connect(lambda: self.select_random_eeg_from_menu())
        self.menuFile.addAction(self.actionRandom)        
        self.actionscoring_load = QtWidgets.QAction(MainWindow)
        self.actionscoring_load.setObjectName("actionscoring_load")
        self.actionscoring_load.triggered.connect(lambda: self.load_scorin_file_from_menu())
        self.menuFile.addAction(self.actionscoring_load)
        self.actionSave = QtWidgets.QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSave.triggered.connect(lambda: self.saveSleepStages())
        self.menuFile.addAction(self.actionSave)

        # Edits menu
        self.menuEdit           = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menubar.addAction(self.menuEdit.menuAction())

        self.actionChannels     = QtWidgets.QAction(MainWindow)
        self.actionChannels.setObjectName("actionChannels")
        self.actionChannels.triggered.connect(lambda: self.scaleChannels())
        self.menuEdit.addAction(self.actionChannels)
        self.actionAnnotations  = QtWidgets.QAction(MainWindow)
        self.actionAnnotations.setObjectName("actionAnnotations")
        self.actionAnnotations.triggered.connect(lambda: self.edit_annotations())
        self.menuEdit.addAction(self.actionAnnotations)
        self.actionEEG          = QtWidgets.QAction(MainWindow)
        self.actionEEG.setObjectName("actionEEG")     
        self.actionEEG.triggered.connect(lambda: self.configuration_pop_up())      
        self.menuEdit.addAction(self.actionEEG)

        # Sleep stages menu
        self.menuStages         = QtWidgets.QMenu(self.menubar)
        self.menuStages.setObjectName("menuStages")
        self.menubar.addAction(self.menuStages.menuAction())

        self.actionN1           = QtWidgets.QAction(MainWindow)
        self.actionN1.setObjectName("actionN1")
        self.actionN1.triggered.connect(lambda: self.scoreN1())
        self.menuStages.addAction(self.actionN1)
        self.actionN2           = QtWidgets.QAction(MainWindow)
        self.actionN2.setObjectName("actionN2")
        self.actionN2.triggered.connect(lambda: self.scoreN2())
        self.menuStages.addAction(self.actionN2)
        self.actionN3           = QtWidgets.QAction(MainWindow)
        self.actionN3.setObjectName("actionN3")
        self.actionN3.triggered.connect(lambda: self.scoreN3())
        self.menuStages.addAction(self.actionN3)
        self.actionWake         = QtWidgets.QAction(MainWindow)
        self.actionWake.setObjectName("actionWake")
        self.actionWake.triggered.connect(lambda: self.scoreWake())
        self.menuStages.addAction(self.actionWake)
        self.actionREM          = QtWidgets.QAction(MainWindow)
        self.actionREM.setObjectName("actionREM")
        self.actionREM.triggered.connect(lambda: self.scoreREM())
        self.menuStages.addAction(self.actionREM)        
        self.actionUncertainty  = QtWidgets.QAction(MainWindow)
        self.actionUncertainty.setObjectName("actionUncertainty")  
        self.actionUncertainty.triggered.connect(lambda: self.scoring_uncertainty())      
        self.menuStages.addAction(self.actionUncertainty)
        self.menuStages.addSeparator()
        self.actionArtefacts    = QtWidgets.QAction(MainWindow)
        self.actionArtefacts.setObjectName("actionArtefacts")   
        self.actionArtefacts.triggered.connect(lambda: self.label_artefacts())   
        self.menuStages.addAction(self.actionArtefacts)

        # Bring together
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
     
     
        # ***************
        # *** Toolbar ***
        toolbar = QtWidgets.QToolBar(MainWindow)
        toolbar.setObjectName("toolbar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)

        # Jump to epoch spinbox
        toolbar.addWidget(QLabel("Jump to epoch:")) 
        self.tool_epochjump = QSpinBox() 
        self.tool_epochjump.valueChanged.connect(self.jump_to_epoch)
        toolbar.addWidget(self.tool_epochjump)

        # Space
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        spacer.setFixedWidth(10)        
        toolbar.addWidget(spacer)    

        # Next unscored epoch button     
        self.tool_nextunscored = QPushButton("Next unscored epoch")
        self.tool_nextunscored.clicked.connect(self.jump_to_unscored_epoch)
        toolbar.addWidget(self.tool_nextunscored)
        toolbar.addWidget(spacer) 

        # Next uncertain epoch button     
        self.tool_nextuncertain = QPushButton("Next uncertain epoch")
        self.tool_nextuncertain.clicked.connect(self.jump_to_uncertain_epoch)
        toolbar.addWidget(self.tool_nextuncertain)
        toolbar.addWidget(spacer)         

        # Next transition button
        self.tool_nexttransition    = QPushButton("Next transition")
        self.tool_nexttransition.clicked.connect(self.jump_to_transition)
        toolbar.addWidget(self.tool_nexttransition)
        #toolbar.addWidget(spacer) 
        


        # Developer mode
        if self.devmode == 1:
            self.load_eeg_data_and_configuration_and_sleep_scoring(os.path.join(self.default_path_to_eeg_data, 'example_data.mat'))

        # Makes GUI listen to key strokes
        MainWindow.keyPressEvent = self.keyPressEvent        

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.menuStages.setTitle(_translate("MainWindow", "Stages"))

        # File
        self.actionOpen.setText(_translate("MainWindow", "Open EEG file"))
        self.actionOpen.setShortcut(_translate("MainWindow", "Ctrl+O"))       
        self.actionRandom.setText(_translate("MainWindow", "Open random from selected EEG files"))
        self.actionRandom.setShortcut(_translate("MainWindow", "Ctrl+R"))            
        self.actionscoring_load.setText(_translate("MainWindow", "Load previous scoring"))
        self.actionscoring_load.setShortcut(_translate("MainWindow", "Ctrl+Shift+O"))  # Add this line for the shortcut        
        self.actionSave.setText(_translate("MainWindow", "Save to"))
        self.actionSave.setShortcut(_translate("MainWindow", "Ctrl+S"))

        # Stages   
        self.actionN1.setText(_translate("MainWindow", "N1"))
        self.actionN1.setShortcut(_translate("MainWindow", "1"))
        self.actionN2.setText(_translate("MainWindow", "N2"))
        self.actionN2.setShortcut(_translate("MainWindow", "2"))
        self.actionN3.setText(_translate("MainWindow", "N3"))
        self.actionN3.setShortcut(_translate("MainWindow", "3"))
        self.actionWake.setText(_translate("MainWindow", "Wake"))
        self.actionWake.setShortcut(_translate("MainWindow", "W"))
        self.actionREM.setText(_translate("MainWindow", "REM"))
        self.actionREM.setShortcut(_translate("MainWindow", "R"))
        self.actionUncertainty.setText(_translate("MainWindow", "Express uncertainty"))
        self.actionUncertainty.setShortcut(_translate("MainWindow", "Q"))        
        self.actionArtefacts.setText(_translate("MainWindow", "Label artefacts"))
        self.actionArtefacts.setShortcut(_translate("MainWindow", "A"))  # Add this line for the shortcut

        # Edit
        self.actionChannels.setText(_translate("MainWindow", "Edit displayed channels"))
        self.actionChannels.setShortcut(_translate("MainWindow", "Ctrl+C"))
        self.actionEEG.setText(_translate("MainWindow", "General configuration settings"))
        self.actionEEG.setShortcut(_translate("MainWindow", "Ctrl+P"))           
        self.actionAnnotations.setText(_translate("MainWindow", "Edit annotations"))
        self.actionAnnotations.setShortcut(_translate("MainWindow", "Ctrl+E"))  # Add this line for the shortcut




if __name__ == "__main__":
    if current_date > expiration_date:
        # License has expired!
        app = QApplication([])
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText("License has expired!")
        msg_box.exec_()
        sys.exit(1)
    else:
        app         = QtWidgets.QApplication(sys.argv)
        MainWindow  = QtWidgets.QMainWindow()
        ui          = Ui_MainWindow()
        ui.setupUi(MainWindow)
        MainWindow.activateWindow()  # Add this line to make the window active
        MainWindow.show()
        sys.exit(app.exec_())
