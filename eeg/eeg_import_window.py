import os
from PySide6.QtWidgets import QFileDialog
from .load_wrapper import load_wrapper


def eeg_import_window(ui, MainWindow, datatype):
    if datatype == "eeglab":
        datatype_to_show = "*.mat"
    if datatype == "r09":
        datatype_to_show = "*.r09"
    if datatype == "edf":
        datatype_to_show = "*.edf"

    name_of_eegfile, _ = QFileDialog.getOpenFileName(
        None, "Open File", ui.default_data_path, datatype_to_show
    )
    ui.filename, suffix = os.path.splitext(name_of_eegfile)
    ui.default_data_path = os.path.dirname(name_of_eegfile)
    MainWindow.setWindowTitle(f"Scoring Hero v.{ui.version[0]}.{ui.version[1]}.{ui.version[2]} ({os.path.basename(name_of_eegfile)})")
    load_wrapper(ui, datatype)
