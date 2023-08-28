import json, os
from PySide6.QtWidgets import QFileDialog


def write_scoring_popup(ui):
    name_of_scoringfile, _ = QFileDialog.getSaveFileName(
        None, "Write scoring file", ui.default_data_path, "*json"
    )
    ui.filename, _ = os.path.splitext(name_of_scoringfile)
    write_scoring_wrapper(ui)


def write_scoring_wrapper(ui):
    write_scoring(f"{ui.filename}.json", ui.stages, ui.annotations)


def write_scoring(scoring_filename, stages, annotations):
    with open(scoring_filename, "w") as file:
        json.dump([stages, annotations], file, indent=1)
