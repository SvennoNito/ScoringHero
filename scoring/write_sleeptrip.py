import csv, os
from PySide6.QtWidgets import QFileDialog, QMessageBox


# Sleeptrip digit mapping (from load_sleeptrip.py mapping_str, inverted)
STAGE_TO_DIGIT = {
    'Wake': 0,
    'N1':   1,
    'N2':   2,
    'N3':   3,
    'REM':  5,
}


def write_sleeptrip(ui):
    default_path = os.path.join(ui.default_data_path, f"{os.path.basename(ui.filename)}.csv")
    csv_filename, _ = QFileDialog.getSaveFileName(
        None, "Export Sleeptrip scoring", default_path, "CSV files (*.csv)"
    )
    if not csv_filename:
        return

    try:
        with open(csv_filename, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            for stage in ui.stages:
                digit = STAGE_TO_DIGIT.get(stage.get("stage"), '')
                artifact = 0 if stage.get("clean", 1) else 1
                writer.writerow([digit, artifact])
    except Exception as e:
        error_message = (
            f"An error occurred while writing the Sleeptrip export file\n"
            f"{csv_filename}:\n\n{str(e)}"
        )
        QMessageBox.critical(ui, "Error", error_message)
