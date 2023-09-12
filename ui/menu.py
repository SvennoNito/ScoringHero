from PySide6.QtCore import QCoreApplication


def setup_menu(ui, MainWindow):
    _translate = QCoreApplication.translate
    ui.menu_file.setTitle(_translate("MainWindow", "File"))
    ui.menu_stages.setTitle(_translate("MainWindow", "Stages"))
    ui.menu_labels.setTitle(_translate("MainWindow", "Labels"))
    ui.menu_utils.setTitle(_translate("MainWindow", "Utilities"))
    ui.menu_config.setTitle(_translate("MainWindow", "Configuration"))

    # File
    ui.action_load_eeglab.setText(
        _translate("MainWindow", "Load EEGLAB structure (.mat)")
    )
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
    ui.action_express_uncertainty.setText(
        _translate("MainWindow", "Express uncertainty")
    )
    ui.action_express_uncertainty.setShortcut(_translate("MainWindow", "Q"))

    # Annotations
    ui.action_artefact.setText(_translate("MainWindow", "Artefact"))
    ui.action_artefact.setShortcut(_translate("MainWindow", "A"))
    ui.action_F1.setText(_translate("MainWindow", "Event 1"))
    ui.action_F1.setShortcut(_translate("MainWindow", "F1"))
    ui.action_F2.setText(_translate("MainWindow", "Event 2"))
    ui.action_F2.setShortcut(_translate("MainWindow", "F2"))
    ui.action_F3.setText(_translate("MainWindow", "Event 3"))
    ui.action_F3.setShortcut(_translate("MainWindow", "F3"))
    ui.action_F4.setText(_translate("MainWindow", "Event 4"))
    ui.action_F4.setShortcut(_translate("MainWindow", "F4"))
    ui.action_F5.setText(_translate("MainWindow", "Event 5"))
    ui.action_F5.setShortcut(_translate("MainWindow", "F5"))
    ui.action_F6.setText(_translate("MainWindow", "Event 6"))
    ui.action_F6.setShortcut(_translate("MainWindow", "F6"))
    ui.action_F7.setText(_translate("MainWindow", "Event 7"))
    ui.action_F7.setShortcut(_translate("MainWindow", "F7"))
    ui.action_F8.setText(_translate("MainWindow", "Event 8"))
    ui.action_F8.setShortcut(_translate("MainWindow", "F8"))
    ui.action_F9.setText(_translate("MainWindow", "Event 9"))
    ui.action_F9.setShortcut(_translate("MainWindow", "F9"))
    # Utilities
    ui.action_zoom.setText(_translate("MainWindow", "Zoom on selected EEG"))
    ui.action_zoom.setShortcut(_translate("MainWindow", "Z"))
