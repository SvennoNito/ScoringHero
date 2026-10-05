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

    if extra_files:
        base_names = ", ".join(os.path.basename(f) for f in name_of_eegfiles)
        MainWindow.setWindowTitle(f"Scoring Hero v.{ui.version[0]}.{ui.version[1]}.{ui.version[2]} ({len(name_of_eegfiles)} files: {os.path.basename(primary_file)}, ...)")
    else:
        MainWindow.setWindowTitle(f"Scoring Hero v.{ui.version[0]}.{ui.version[1]}.{ui.version[2]} ({os.path.basename(primary_file)})")

    def on_done():
        # Enable the menus once the data is loaded
        ui.menu_stages.setEnabled(True)
        ui.menu_labels.setEnabled(True)
        ui.menu_utils.setEnabled(True)
        ui.menu_autoscore.setEnabled(True)
        ui.menu_config.setEnabled(True)

        # Enable toolbar once the data is loaded
        ui.toolbar_jump_to_epoch.setEnabled(True)
        ui.tool_nextunscored.setEnabled(True)
        ui.tool_nextuncertain.setEnabled(True)
        ui.tool_nexttransition.setEnabled(True)
        ui.tool_nextevent.setEnabled(True)
        ui.tool_nexthuman.setEnabled(True)

        # Enable sliders
        ui.HypnogramSlider.enable_slider()

    def on_error(e):
        QMessageBox.critical(None, "File loading error", str(e))

    load_wrapper_busy(ui, datatype, extra_files, on_done, on_error)
    