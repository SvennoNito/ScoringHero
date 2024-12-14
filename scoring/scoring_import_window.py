import os
from PySide6.QtWidgets import QFileDialog
from utilities.refresh_gui import refresh_gui
from .load_scoring import load_scoring
from .events_to_ui import events_to_ui


def scoring_import_window(ui, filetype):
    if filetype == "scoringhero":
        datatype = "*.json"
    if filetype == "vis":
        datatype = "*.vis"
    if filetype == "yasa":
        datatype = "*.txt"

    name_of_scoringfile, _ = QFileDialog.getOpenFileName(
        None, "Open Scoring File", ui.default_data_path, datatype
    )

    # Check if the user clicked "Cancel"
    if not name_of_scoringfile:
        return  # Exit the function if no file is selected

    ui.filename, suffix = os.path.splitext(name_of_scoringfile)
    ui.default_data_path = os.path.dirname(name_of_scoringfile)
    ui.stages, events = load_scoring(
        name_of_scoringfile, ui.config[0]["Epoch_length_s"], ui.numepo, filetype
    )
    events_to_ui(ui, events)
    refresh_gui(ui)
    ui.HypnogramWidget.draw_hypnogram(ui)
