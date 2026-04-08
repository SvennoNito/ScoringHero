import os
from PySide6.QtWidgets import (
    QFileDialog, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QScrollArea, QWidget
)
from events.draw_event_in_this_epoch import draw_event_in_this_epoch
from .load_scoring import load_scoring
from .load_sleeptrip import load_sleeptrip
from .load_sleeptrip_events import load_sleeptrip_events
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


class SleeptripEventMappingDialog(QDialog):
    def __init__(self, event_labels, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Map SleepTrip Events to ScoringHero Format")

        outer_layout = QVBoxLayout()
        outer_layout.addWidget(QLabel(
            "Assign each event type to a ScoringHero event slot\n"
            "(or 'Skip' to ignore it):"
        ))

        # Scrollable area in case there are many event types
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)

        self.combos = {}
        options = ["Skip"] + [f"F{i}" for i in range(1, 13)]

        for i, label in enumerate(event_labels):
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            combo = QComboBox()
            combo.addItems(options)
            # Auto-assign first 12 event types to F1..F12 as default
            if i < 12:
                combo.setCurrentIndex(i + 1)
            row.addWidget(combo)
            inner_layout.addLayout(row)
            self.combos[label] = combo

        inner_layout.addStretch()
        scroll.setWidget(inner_widget)
        outer_layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        import_btn = QPushButton("Import")
        cancel_btn = QPushButton("Cancel")
        import_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(cancel_btn)
        outer_layout.addLayout(btn_layout)

        self.setLayout(outer_layout)
        self.resize(400, min(80 + 40 * len(event_labels), 500))

    def get_mapping(self):
        """Returns dict mapping event_label -> (digit, slot_name) or None if Skip."""
        mapping = {}
        for label, combo in self.combos.items():
            text = combo.currentText()
            if text == "Skip":
                mapping[label] = None
            else:
                digit = int(text[1:])  # F1 -> 1, F12 -> 12
                mapping[label] = (digit, text)
        return mapping


def scoring_import_window(ui, filetype):
    if filetype == "scoringhero":
        datatype = "*.json"
    if filetype == "vis":
        datatype = "*.vis"
    if filetype == "yasa":
        datatype = "*.txt"
    if filetype == "sleeptrip":
        datatype = "*.csv"
    if filetype == "sleeptrip_events":
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

    ui.default_data_path = os.path.dirname(name_of_scoringfile)
    if filetype != "sleeptrip_events":
        ui.filename, suffix = os.path.splitext(name_of_scoringfile)

    if filetype == "sleeptrip_events":
        raw_events, unique_labels = load_sleeptrip_events(name_of_scoringfile)

        dialog = SleeptripEventMappingDialog(unique_labels)
        if not dialog.exec():
            return

        mapping = dialog.get_mapping()
        epolen = ui.config[0]["Epoch_length_s"]

        events = []
        for ev in raw_events:
            label = ev["event"]
            if mapping.get(label) is None:
                continue
            digit, slot_name = mapping[label]
            start_epoch = int(ev["start"] / epolen)
            end_epoch = int(ev["stop"] / epolen)
            epoch_list = list(range(start_epoch + 1, end_epoch + 2))
            events.append({
                "digit": digit,
                "event": label,
                "start": ev["start"],
                "end": ev["stop"],
                "epoch": epoch_list,
            })

        events_to_ui(ui, events)
        ui.HypnogramWidget.draw_hypnogram(ui)
        ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)
        for container in ui.AnnotationContainer:
            draw_event_in_this_epoch(ui, container)
        return

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

    ui.HypnogramWidget.draw_hypnogram(ui)
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)
