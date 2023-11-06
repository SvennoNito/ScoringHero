import os
from PySide6.QtWidgets import QFileDialog
from .write_scoring import write_scoring


def scoring_export_window(ui):
    name_of_scoringfile, _ = QFileDialog.getSaveFileName(
        None, "Write scoring file", os.path.join(ui.default_data_path, f'{ui.filename}.json'), "*json"
    )
    ui.filename, _ = os.path.splitext(name_of_scoringfile)
    ui.default_data_path = os.path.dirname(name_of_scoringfile)
    write_scoring(ui)
