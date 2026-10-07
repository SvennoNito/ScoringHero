"""Shared pre-run dialogs for autoscorers (GSSC, NIDRA)."""

from PySide6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QLabel, QCheckBox, QDialogButtonBox,
)

from scoring_model.formats import GSSC_STAGES

_EPOCH_TEXT = {
    "GSSC": (
        "GSSC uses 30-second epochs, but your epoch length is {epolen}s.\n\n"
        "GSSC scores will be mapped onto your epoch grid automatically.\n\n"
        "You can adjust the epoch length in the Configuration panel "
        "if you prefer 30s epochs."
    ),
    "NIDRA": (
        "The NIDRA models use 30-second epochs, but your epoch length is "
        "{epolen}s.\n\nThe scores will be mapped onto your epoch grid "
        "automatically.\n\nYou can adjust the epoch length in the "
        "Configuration panel if you prefer 30s epochs."
    ),
}


def ask_staging_options(ui, method):
    """Run epoch-length and existing-scores dialogs for `method` ("GSSC" or "NIDRA").

    Returns (mode, overwrite_stages) with mode in {"overwrite", "selective",
    "fill_missing"} and overwrite_stages a set or None; None if cancelled.
    """
    epolen = ui.config[0]["Epoch_length_s"]
    if epolen != 30:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Epoch length mismatch")
        msg.setText(_EPOCH_TEXT[method].format(epolen=epolen))
        btn_continue = msg.addButton("Continue", QMessageBox.AcceptRole)
        msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.exec()
        if msg.clickedButton() != btn_continue:
            return None

    scored_count = sum(1 for stage in ui.scoring.stages() if stage is not None)
    if scored_count == 0:
        return "overwrite", None

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Existing scores detected")
    msg.setText(
        f"{scored_count} epoch(s) already have sleep scores.\n"
        "How would you like to proceed?"
    )
    btn_overwrite = msg.addButton("Overwrite all", QMessageBox.AcceptRole)
    btn_selective = msg.addButton("Overwrite selected stages...", QMessageBox.AcceptRole)
    btn_fill = msg.addButton("Fill missing only", QMessageBox.AcceptRole)
    msg.addButton("Cancel", QMessageBox.RejectRole)
    msg.exec()

    clicked = msg.clickedButton()
    if clicked == btn_overwrite:
        return "overwrite", None
    if clicked == btn_selective:
        stages = _ask_selective_stages()
        return ("selective", stages) if stages is not None else None
    if clicked == btn_fill:
        return "fill_missing", None
    return None


def _ask_selective_stages(parent=None):
    """Show dialog to select which existing stages to overwrite. Returns set or None."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Select stages to overwrite")
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("Overwrite epochs currently scored as:"))

    checkboxes = {}
    for stage in GSSC_STAGES.values():
        cb = QCheckBox(stage)
        checkboxes[stage] = cb
        layout.addWidget(cb)

    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)

    if dialog.exec() == QDialog.Accepted:
        selected = {s for s, cb in checkboxes.items() if cb.isChecked()}
        return selected if selected else None
    return None
