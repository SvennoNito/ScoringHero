import os
from PySide6.QtWidgets import QFileDialog, QMessageBox
from .load_wrapper import load_wrapper_busy


def eeg_import_window(ui, MainWindow, datatype):
    if datatype == "eeglab":
        datatype_to_show = "*.mat"
    if datatype == "r09":
        datatype_to_show = "*.r09"
    if datatype == "edf":
        datatype_to_show = "*.edf"
    if datatype == "edfvolt":
        datatype_to_show = "*.edf"

    name_of_eegfiles, _ = QFileDialog.getOpenFileNames(
        None, "Open File(s)", ui.default_data_path, datatype_to_show
    )

    # Check if the user clicked "Cancel"
    if not name_of_eegfiles:
        return  # Exit the function if no file is selected

    primary_file = name_of_eegfiles[0]
    extra_files = name_of_eegfiles[1:]

    ui.filename, suffix = os.path.splitext(primary_file)
    ui.default_data_path = os.path.dirname(primary_file)
    ui.eeg_file_name = os.path.basename(primary_file)
    ui.eeg_extra_files = len(extra_files)

    def on_error(e):
        QMessageBox.critical(None, "File loading error", str(e))

    load_wrapper_busy(ui, datatype, extra_files, on_error)
    