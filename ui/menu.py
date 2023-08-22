from PySide6.QtCore import QCoreApplication

def setup_menu(ui, MainWindow):

    _translate = QCoreApplication.translate
    MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
    ui.menu_file.setTitle(_translate("MainWindow", "File"))
    ui.menu_edit.setTitle(_translate("MainWindow", "Edit"))
    ui.menu_stages.setTitle(_translate("MainWindow", "Stages"))

    # File
    ui.action_load_eeglab.setText(_translate("MainWindow", "Load EEGLAB structure (.mat)"))
    ui.action_load_eeglab.setShortcut(_translate("MainWindow", "Ctrl+O"))       
    ui.action_load_scoring.setText(_translate("MainWindow", "Load previous scoring"))
    ui.action_load_scoring.setShortcut(_translate("MainWindow", "Ctrl+Shift+O"))         
    ui.action_save_scoring.setText(_translate("MainWindow", "Save to"))
    ui.action_save_scoring.setShortcut(_translate("MainWindow", "Ctrl+S"))

    # Stages   
    ui.action_N1.setText(_translate("MainWindow", "N1"))
    ui.action_N1.setShortcut(_translate("MainWindow", "1"))
    ui.action_N2.setText(_translate("MainWindow", "N2"))
    ui.action_N2.setShortcut(_translate("MainWindow", "2"))
    ui.action_N3.setText(_translate("MainWindow", "N3"))
    ui.action_N3.setShortcut(_translate("MainWindow", "3"))
    ui.action_wake.setText(_translate("MainWindow", "Wake"))
    ui.action_wake.setShortcut(_translate("MainWindow", "W"))
    ui.action_REM.setText(_translate("MainWindow", "REM"))
    ui.action_REM.setShortcut(_translate("MainWindow", "R"))
    ui.action_express_uncertainty.setText(_translate("MainWindow", "Express uncertainty"))
    ui.action_express_uncertainty.setShortcut(_translate("MainWindow", "Q"))        
    ui.action_label_artefact.setText(_translate("MainWindow", "Mark box as artefact"))
    ui.action_label_artefact.setShortcut(_translate("MainWindow", "A"))  # Add this line for the shortcut
    ui.action_zoon_on_EEG.setText(_translate("MainWindow", "Zoom on selected EEG"))
    ui.action_zoon_on_EEG.setShortcut(_translate("MainWindow", "Z"))  # Add this line for the shortcut

    # Edit
    ui.action_edit_channels.setText(_translate("MainWindow", "Edit displayed channels"))
    ui.action_edit_channels.setShortcut(_translate("MainWindow", "Ctrl+C"))
    ui.action_edit_config.setText(_translate("MainWindow", "General configuration settings"))
    ui.action_edit_config.setShortcut(_translate("MainWindow", "Ctrl+P"))           
    ui.action_edit_annotations.setText(_translate("MainWindow", "Edit annotations"))
    ui.action_edit_annotations.setShortcut(_translate("MainWindow", "Ctrl+E"))  # Add this line for the shortcut
