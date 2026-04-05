import os
from PySide6.QtWidgets import (
    QFileDialog, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton
)
from utilities.refresh_gui import refresh_gui
from .load_scoring import load_scoring
from .load_sleeptrip import load_sleeptrip
from .events_to_ui import events_to_ui


class EpochEventImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Per-Epoch Event Column")

        layout = QVBoxLayout()

        layout.addWidget(QLabel(
            "The file contains a per-epoch event column (second column).\n"
            "Would you like to import it as an event?"
        ))

        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("Assign to event:"))
        self.combo = QComboBox()
        self.combo.addItems(["A"] + [f"F{i}" for i in range(1, 13)])
        combo_layout.addWidget(self.combo)
        layout.addLayout(combo_layout)

        btn_layout = QHBoxLayout()
        import_btn = QPushButton("Import")
        skip_btn = QPushButton("Skip")
        import_btn.clicked.connect(self.accept)
        skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(skip_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def selected_digit(self):
        return self.combo.currentIndex()  # 0=A, 1=F1, ..., 12=F12

    def selected_label(self):
        text = self.combo.currentText()
        return "Artifact" if text == "A" else text


def scoring_import_window(ui, filetype):
    if filetype == "scoringhero":
        datatype = "*.json"
    if filetype == "vis":
        datatype = "*.vis"
    if filetype == "yasa":
        datatype = "*.txt"
    if filetype == "sleeptrip":
        datatype = "*.csv"
    if filetype == "sleepyland":
        datatype = "*.annot"
    if filetype == "gssc":
        datatype = "*.csv"

    name_of_scoringfile, _ = QFileDialog.getOpenFileName(
        None, "Open Scoring File", ui.default_data_path, datatype
    )

    # Check if the user clicked "Cancel"
    if not name_of_scoringfile:
        return  # Exit the function if no file is selected

    ui.filename, suffix = os.path.splitext(name_of_scoringfile)
    ui.default_data_path = os.path.dirname(name_of_scoringfile)

    if filetype == "sleeptrip":
        epolen = ui.config[0]["Epoch_length_s"]
        ui.stages, epoch_event_col = load_sleeptrip(name_of_scoringfile, epolen, ui.numepo)

        events = []
        if epoch_event_col and any(v == 1 for v in epoch_event_col):
            dialog = EpochEventImportDialog()
            if dialog.exec():
                digit = dialog.selected_digit()
                label = dialog.selected_label()
                for epoch_idx, val in enumerate(epoch_event_col):
                    if val == 1:
                        events.append({
                            "digit": digit,
                            "event": label,
                            "start": epoch_idx * epolen,
                            "end": (epoch_idx + 1) * epolen,
                            "epoch": [epoch_idx + 1],
                        })

        events_to_ui(ui, events)
    else:
        ui.stages, events = load_scoring(
            name_of_scoringfile, ui.config[0]["Epoch_length_s"], ui.numepo, filetype
        )
        events_to_ui(ui, events)

    refresh_gui(ui)
    ui.HypnogramWidget.draw_hypnogram(ui)
