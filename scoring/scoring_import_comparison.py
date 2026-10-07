import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox
)

from scoring_model.formats import FORMATS
from utilities.epoch_status import comparison_display_name
from widgets.resolveDialog import resolve_loaded

class _FormatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Comparison Scoring Format")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select the format of the comparison scoring file:"))

        row = QHBoxLayout()
        row.addWidget(QLabel("Format:"))
        self.combo = QComboBox()
        self.combo.addItems([fmt.label for fmt in FORMATS.values()])
        row.addWidget(self.combo)
        layout.addLayout(row)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def selection(self):
        return list(FORMATS.values())[self.combo.currentIndex()]


def scoring_import_comparison(ui):
    if getattr(ui, "scoring", None) is None:
        return

    dialog = _FormatDialog()
    if not dialog.exec():
        return

    fmt = dialog.selection()
    name_of_scoringfile, _ = QFileDialog.getOpenFileName(
        None, "Open Comparison Scoring File", ui.default_data_path, fmt.file_filter
    )
    if not name_of_scoringfile:
        return

    ui.default_data_path = os.path.dirname(name_of_scoringfile)

    try:
        loaded = fmt.loader(name_of_scoringfile)
    except Exception as e:
        QMessageBox.critical(ui, "Error", f"The scoring file\n{name_of_scoringfile}\ncould not be read:\n\n{e}")
        return
    scoring = resolve_loaded(ui, loaded, ui.numepo, ui.config[0]["Epoch_length_s"])
    if scoring is None:
        return  # cancelled: abort, nothing changes

    ui.scoring_comparison = scoring
    ui.comparison_name = comparison_display_name(name_of_scoringfile)

    ui.action_remove_comparison.setEnabled(True)
    ui.action_comparison_stats.setEnabled(True)
    ui.tool_nextdisagreement.setEnabled(True)

    ui.HypnogramWidget.draw_hypnogram(ui)
    ui.StatusReadout.update(ui)


def clear_comparison(ui):
    """Drop the comparison scoring and disable its actions (no redraw)."""
    ui.scoring_comparison = None
    ui.comparison_name = None

    ui.action_remove_comparison.setEnabled(False)
    ui.action_comparison_stats.setEnabled(False)
    ui.tool_nextdisagreement.setEnabled(False)


def remove_comparison_scoring(ui):
    clear_comparison(ui)
    ui.HypnogramWidget.draw_hypnogram(ui)
    ui.StatusReadout.update(ui)
