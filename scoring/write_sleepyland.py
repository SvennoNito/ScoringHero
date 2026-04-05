import os
from PySide6.QtWidgets import QFileDialog, QMessageBox


# Inverted from load_sleepyland.py mapping_str: {'W': 'Wake', 'N1': 'N1', 'N2': 'N2', 'N3': 'N3', 'R': 'REM'}
STAGE_TO_KEY = {
    'Wake': 'W',
    'N1':   'N1',
    'N2':   'N2',
    'N3':   'N3',
    'REM':  'R',
}

# Which confidence field each stage maps to in the meta string
STAGE_TO_CONF_KEY = {
    'Wake': 'pW',
    'N1':   'pN1',
    'N2':   'pN2',
    'N3':   'pN3',
    'REM':  'pR',
}


def _build_meta(stage_name, confidence):
    """Build meta string with confidence placed in the correct slot."""
    conf_value = confidence if confidence is not None else 1.0
    all_keys = ['pW', 'pN1', 'pN2', 'pN3', 'pR']
    active_key = STAGE_TO_CONF_KEY.get(stage_name)
    parts = []
    for k in all_keys:
        parts.append(f"{k}={conf_value if k == active_key else 0.0}")
    return '; '.join(parts)


def write_sleepyland(ui):
    default_path = os.path.join(ui.default_data_path, f"{os.path.basename(ui.filename)}.annot")
    annot_filename, _ = QFileDialog.getSaveFileName(
        None, "Export Sleepyland scoring", default_path, "Annotation files (*.annot)"
    )
    if not annot_filename:
        return

    epolen = ui.data.get("epolen", 30)
    try:
        with open(annot_filename, "w") as f:
            f.write("Epoch\tStage\tStart\tEnd\tDuration\tMeta\n")
            for i, stage in enumerate(ui.stages):
                stage_name = stage.get("stage")
                key        = STAGE_TO_KEY.get(stage_name, 'W')
                start      = i * epolen
                end        = (i + 1) * epolen
                meta       = _build_meta(stage_name, stage.get("confidence"))
                f.write(f"{i + 1}\t{key}\t{start}\t{end}\t{epolen}\t{meta}\n")
    except Exception as e:
        QMessageBox.critical(ui, "Error",
            f"An error occurred while writing the Sleepyland export file\n{annot_filename}:\n\n{str(e)}")
