import os
from PySide6.QtWidgets import QFileDialog, QMessageBox
from scoring_model.formats import FORMATS
from .write_scoring import write_scoring


def scoring_export_window(ui):
    name_of_scoringfile, _ = QFileDialog.getSaveFileName(
        None, "Write scoring file", os.path.join(ui.default_data_path, f'{ui.filename}.json'), "*json"
    )
    ui.filename, _ = os.path.splitext(name_of_scoringfile)
    ui.default_data_path = os.path.dirname(name_of_scoringfile)
    write_scoring(ui)


def export_scoring(ui, format_name):
    """Export the primary scoring in one of the FORMATS; the file dialog lives here."""
    fmt = FORMATS[format_name]
    extension = fmt.file_filter[1:]
    default_path = os.path.join(ui.default_data_path, f"{os.path.basename(ui.filename)}{extension}")
    path, _ = QFileDialog.getSaveFileName(None, f"Export {fmt.label}", default_path, fmt.label)
    if not path:
        return
    try:
        fmt.writer(ui.scoring, path)
    except Exception as e:
        QMessageBox.critical(ui, "Error", f"An error occurred while writing the export file\n{path}:\n\n{e}")
