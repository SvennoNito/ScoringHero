import os
from PySide6.QtWidgets import QFileDialog


def scoring_export_window(ui):
    name_of_scoringfile, _ = QFileDialog.getSaveFileName(
        None, "Write scoring file", ui.default_data_path, "*json"
    )
    ui.filename, _ = os.path.splitext(name_of_scoringfile)
    write_scoring(ui)
