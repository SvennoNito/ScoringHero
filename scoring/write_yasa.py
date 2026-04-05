import os
from PySide6.QtWidgets import QFileDialog, QMessageBox


# YASA canonical output labels
STAGE_TO_LABEL = {
    'Wake': 'W',
    'N1':   'N1',
    'N2':   'N2',
    'N3':   'N3',
    'REM':  'R',
}


def write_yasa(ui):
    default_path = os.path.join(ui.default_data_path, f"{os.path.basename(ui.filename)}.txt")
    txt_filename, _ = QFileDialog.getSaveFileName(
        None, "Export YASA scoring", default_path, "Text files (*.txt)"
    )
    if not txt_filename:
        return

    try:
        with open(txt_filename, "w") as f:
            for stage in ui.stages:
                label = STAGE_TO_LABEL.get(stage.get("stage"), '')
                f.write(f"{label}\n")
    except Exception as e:
        QMessageBox.critical(ui, "Error",
            f"An error occurred while writing the YASA export file\n{txt_filename}:\n\n{str(e)}")
