import csv, os
from PySide6.QtWidgets import QFileDialog, QMessageBox


# Inverted from load_gssc.py mapping_str: {0: 'Wake', 1: 'N1', 2: 'N2', 3: 'N3', 4: 'REM'}
STAGE_TO_INT = {
    'Wake': 0,
    'N1':   1,
    'N2':   2,
    'N3':   3,
    'REM':  4,
}


def write_gssc(ui):
    default_path = os.path.join(ui.default_data_path, f"{os.path.basename(ui.filename)}.csv")
    csv_filename, _ = QFileDialog.getSaveFileName(
        None, "Export GSSC scoring", default_path, "CSV files (*.csv)"
    )
    if not csv_filename:
        return

    try:
        with open(csv_filename, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Epoch", "Start", "Stage", "pWake", "pN1", "pN2", "pN3", "pREM"])
            for i, stage in enumerate(ui.stages):
                stage_name = stage.get("stage")
                stage_int  = STAGE_TO_INT.get(stage_name, 0)
                confidence = stage.get("confidence")
                conf_value = confidence if confidence is not None else 1.0
                # Place stored confidence in the correct column, 0.0 elsewhere
                confs = [conf_value if j == stage_int else 0.0 for j in range(5)]
                epolen = ui.data.get("epolen", 30)
                writer.writerow([i + 1, i * epolen, stage_int] + confs)
    except Exception as e:
        QMessageBox.critical(ui, "Error",
            f"An error occurred while writing the GSSC export file\n{csv_filename}:\n\n{str(e)}")
