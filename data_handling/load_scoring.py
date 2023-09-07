import os, json
import numpy as np
from PySide6.QtWidgets import QFileDialog
from .default_scoring import default_scoring
from utilities.refresh_gui import refresh_gui 


def load_scoring(scoring_filename, epolen, numepo):
    if os.path.exists(scoring_filename):
        with open(scoring_filename, "r") as file:
            json_data       = json.load(file)
            annotations     = json_data[1]
            scoring_data    = json_data[0]
    else:
        annotations     = []
        scoring_data    = default_scoring(epolen, numepo)
    return scoring_data, annotations


def load_scoring_qdialog(ui):
    name_of_scoringfile, _ = QFileDialog.getOpenFileName(
        None, "Open Scoring File", ui.default_data_path, "*.json"
    )
    ui.filename, suffix = os.path.splitext(name_of_scoringfile)
    ui.stages, events = load_scoring(f"{ui.filename}.json",  ui.config[0]["Epoch_length_s"], ui.numepo)
    events_to_ui(ui, events)
    refresh_gui(ui)
    ui.HypnogramWidget.draw_hypnogram(ui.stages, ui.numepo, ui.config, ui.swa)


def events_to_ui(ui, events):
    event_digits = [item['digit'] for item in events]
    for event_digit in set(event_digits):
        container_index = np.where(np.array(event_digits) == event_digit)[0].tolist()
        for container in np.array(events)[container_index]:
            ui.AnnotationContainer[event_digit].label = container['event']
            ui.AnnotationContainer[event_digit].borders.append([container['start'], container['end']])
            ui.AnnotationContainer[event_digit].epochs.append(container['epoch'])    
