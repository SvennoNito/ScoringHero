import os
from PySide6.QtWidgets import QFileDialog
from .load_wrapper import load_wrapper


def eeg_import_window(ui, datatype):
    name_of_eegfile, _ = QFileDialog.getOpenFileName(
        None, "Open File", ui.default_data_path, "*.mat"
    )
    ui.filename, suffix = os.path.splitext(name_of_eegfile)
    load_wrapper(ui, datatype)
