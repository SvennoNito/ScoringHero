import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog
)

from .load_scoring import load_scoring
from .load_sleeptrip import load_sleeptrip


_FORMATS = [
    ("ScoringHero (.json)",                                  "scoringhero", "*.json"),
    ("Zurich Scoring (.vis)",                                "vis",         "*.vis"),
    ("YASA (.txt)",                                          "yasa",        "*.txt"),
    ("Sleeptrip (.csv)",                                     "sleeptrip",   "*.csv"),
    ("Sleepyland (.annot)",                                  "sleepyland",  "*.annot"),
    ("Greifswald Sleep Stage Classifier / GSSC (.csv)",      "gssc",        "*.csv"),
]


class _FormatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Comparison Scoring Format")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select the format of the comparison scoring file:"))

        row = QHBoxLayout()
        row.addWidget(QLabel("Format:"))
        self.combo = QComboBox()
        self.combo.addItems([label for label, _, _ in _FORMATS])
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
        _, filetype, file_filter = _FORMATS[self.combo.currentIndex()]
        return filetype, file_filter


def scoring_import_comparison(ui):
    if not getattr(ui, "stages", None):
        return

    dialog = _FormatDialog()
    if not dialog.exec():
        return

    filetype, file_filter = dialog.selection()
    name_of_scoringfile, _ = QFileDialog.getOpenFileName(
        None, "Open Comparison Scoring File", ui.default_data_path, file_filter
    )
    if not name_of_scoringfile:
        return

    ui.default_data_path = os.path.dirname(name_of_scoringfile)

    if filetype == "sleeptrip":
        epolen = ui.config[0]["Epoch_length_s"]
        stages_ref, _ = load_sleeptrip(name_of_scoringfile, epolen, ui.numepo)
    else:
        stages_ref, _ = load_scoring(
            name_of_scoringfile, ui.config[0]["Epoch_length_s"], ui.numepo, filetype
        )

    ui.stages_ref = stages_ref
    _recompute_disagreements(ui)

    ui.action_remove_comparison.setEnabled(True)
    ui.action_comparison_stats.setEnabled(True)
    ui.tool_nextdisagreement.setEnabled(True)

    ui.HypnogramWidget.draw_hypnogram(ui)
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages, ui.stages_ref)


def remove_comparison_scoring(ui):
    ui.stages_ref = None
    ui.disagreement_epochs = []
    ui.disagreement_index = 0

    ui.action_remove_comparison.setEnabled(False)
    ui.action_comparison_stats.setEnabled(False)
    ui.tool_nextdisagreement.setEnabled(False)

    ui.HypnogramWidget.draw_hypnogram(ui)
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages, None)


def _recompute_disagreements(ui):
    n = min(len(ui.stages), len(ui.stages_ref))
    ui.disagreement_epochs = [
        i for i in range(n)
        if ui.stages[i]["digit"] != ui.stages_ref[i]["digit"]
    ]
    ui.disagreement_index = 0
