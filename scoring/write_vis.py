import os
from PySide6.QtWidgets import QFileDialog, QMessageBox


# Inverted from load_vis.py mapping: {'0': 'Wake', '1': 'N1', '2': 'N2', '3': 'N3', 'r': 'REM'}
STAGE_TO_SYMBOL = {
    'Wake': '0',
    'N1':   '1',
    'N2':   '2',
    'N3':   '3',
    'REM':  'r',
}


def write_vis(ui):
    default_path = os.path.join(ui.default_data_path, f"{os.path.basename(ui.filename)}.vis")
    vis_filename, _ = QFileDialog.getSaveFileName(
        None, "Export Zurich scoring", default_path, "VIS files (*.vis)"
    )
    if not vis_filename:
        return

    try:
        with open(vis_filename, "w") as f:
            f.write("0\n")  # offset line
            for i, stage in enumerate(ui.stages):
                symbol = STAGE_TO_SYMBOL.get(stage.get("stage"), '0')
                f.write(f"{i + 1} {symbol}\n")
    except Exception as e:
        QMessageBox.critical(ui, "Error",
            f"An error occurred while writing the VIS export file\n{vis_filename}:\n\n{str(e)}")
