import os
from PySide6.QtWidgets import QFileDialog
from utilities.refresh_gui import refresh_gui
from .load_scoring import load_scoring
from .events_to_ui import events_to_ui


def scoring_import_window(ui):
    name_of_scoringfile, _ = QFileDialog.getOpenFileName(
        None, "Open Scoring File", ui.default_data_path, "*.json"
    )
    ui.filename, suffix = os.path.splitext(name_of_scoringfile)
    ui.stages, events = load_scoring(
        f"{ui.filename}.json", ui.config[0]["Epoch_length_s"], ui.numepo
    )
    events_to_ui(ui, events)
    refresh_gui(ui)
    ui.HypnogramWidget.draw_hypnogram(ui.stages, ui.numepo, ui.config, ui.swa)
