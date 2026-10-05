import csv
import os

from PySide6.QtWidgets import QFileDialog, QMessageBox

# Inverted from load_ezscore.py: 1=N1 2=N2 3=N3 4=REM 5=Wake 6=Artifact
STAGE_TO_INT = {
    "N1":   1,
    "N2":   2,
    "N3":   3,
    "REM":  4,
    "Wake": 5,
}

_ARTIFACT = 6


def write_ezscore(ui):
    """Export the scoring as an ezscore-f hypnogram CSV (one code per epoch).

    This is the format ezscore_demo.py writes: a single column of integers,
    no header. Epochs without a valid sleep stage (unscored, or scored as
    Inconclusive) are exported as ezscore's artifact class, which is the only
    non-stage code the format has.
    """
    default_path = os.path.join(ui.default_data_path, f"{os.path.basename(ui.filename)}_ezscore.csv")
    csv_filename, _ = QFileDialog.getSaveFileName(
        None, "Export ezscore-f hypnogram", default_path, "CSV files (*.csv)"
    )
    if not csv_filename:
        return

    try:
        with open(csv_filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for epoch in ui.stages:
                code = STAGE_TO_INT.get(epoch.get("stage"), _ARTIFACT)
                writer.writerow([code])
    except Exception as exc:
        QMessageBox.critical(
            ui,
            "Error",
            f"An error occurred while writing the ezscore export file\n{csv_filename}:\n\n{exc}",
        )
