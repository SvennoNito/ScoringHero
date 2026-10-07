import os
from PySide6.QtWidgets import (
    QFileDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QScrollArea, QWidget
)
from scoring_model.event_records import (
    add_records, artefact_flag_records, events_from_records, sleeptrip_event_records,
)
from utilities.refresh_gui import _update_export_menu_state
from scoring_model.events import N_SLOTS, Events
from scoring_model.formats import FORMATS
from widgets.resolveDialog import resolve_loaded
from .load_sleeptrip_events import load_sleeptrip_events


class EpochEventImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Per-Epoch Event Column")

        layout = QVBoxLayout()

        layout.addWidget(QLabel(
            "The file contains a per-epoch event column (second column).\n"
            "Would you like to import it as an event?\n"
            "Only slot 0 makes ScoringHero treat the flagged epochs as artefacts."
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


def _replace_with_records(events, records):
    """Sleeptrip import replaces every event: clear all slots, then add the records."""
    for slot in range(N_SLOTS):
        events.clear(slot)
    add_records(events, records)


def scoring_import_window(ui, filetype):
    if filetype == "sleeptrip_events":
        datatype = "*.csv"
    else:
        datatype = FORMATS[filetype].file_filter

    name_of_scoringfile, _ = QFileDialog.getOpenFileName(
        None, "Open Scoring File", ui.default_data_path, datatype
    )

    # Check if the user clicked "Cancel"
    if not name_of_scoringfile:
        return  # Exit the function if no file is selected

    ui.default_data_path = os.path.dirname(name_of_scoringfile)

    if filetype == "sleeptrip_events":
        raw_events, unique_labels = load_sleeptrip_events(name_of_scoringfile)

        dialog = SleeptripEventMappingDialog(unique_labels)
        if not dialog.exec():
            return

        mapping = dialog.get_mapping()
        epolen = ui.config[0]["Epoch_length_s"]

        records = []
        for label, target in mapping.items():
            if target is None:
                continue
            digit, _ = target
            raw = [ev for ev in raw_events if ev["event"] == label]
            records += sleeptrip_event_records(raw, digit, label, epolen)

        ui.edit_events(lambda events: _replace_with_records(events, records))
        return

    epolen = ui.config[0]["Epoch_length_s"]
    try:
        loaded = FORMATS[filetype].loader(name_of_scoringfile)
    except Exception as e:
        QMessageBox.critical(ui, "Error", f"The scoring file\n{name_of_scoringfile}\ncould not be read:\n\n{e}")
        return
    scoring = resolve_loaded(ui, loaded, ui.numepo, epolen)
    if scoring is None:
        return  # cancelled: nothing changes

    ui.filename, _ = os.path.splitext(name_of_scoringfile)
    ui.scoring = scoring

    if filetype == "scoringhero":
        ui.events = events_from_records(loaded.events, epolen, ui.numepo)
    else:
        ui.events = Events(epolen, ui.numepo)
    ui.HypnogramWidget.draw_hypnogram(ui)
    ui.StatusReadout.update(ui)
    _update_export_menu_state(ui)

    if filetype == "sleeptrip":
        flags = loaded.artefact_flags
        if flags and any(v == 1 for v in flags):
            dialog = EpochEventImportDialog()
            if dialog.exec():
                slot, label = dialog.selected_digit(), dialog.selected_label()
                records = artefact_flag_records(flags, slot, label, epolen)
                ui.edit_events(lambda events: add_records(events, records))
                return
    ui.SignalWidget.draw_events(ui.events, ui.this_epoch)
    ui.HypnogramWidget.update_events(ui)
