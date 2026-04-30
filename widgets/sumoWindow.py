from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QGroupBox,
    QDialogButtonBox,
    QListWidget,
    QAbstractItemView,
    QDoubleSpinBox,
    QWidget,
    QCheckBox,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt

# Stage names in display order
_STAGES = ["Wake", "N1", "N2", "N3", "REM", "Inconclusive"]


def _info_label(text, tooltip):
    """Return a QWidget with a field label and a hoverable ⓘ icon."""
    widget = QWidget()
    row = QHBoxLayout(widget)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(5)

    row.addWidget(QLabel(text))

    icon = QLabel("ⓘ")
    icon.setStyleSheet("color: #5ba3d9; font-weight: bold;")
    icon.setToolTip(tooltip)
    icon.setToolTipDuration(0)
    icon.setCursor(Qt.WhatsThisCursor)
    row.addWidget(icon)
    row.addStretch()

    return widget


class SumoWindow(QDialog):
    """Settings dialog for SUMO spindle detection (Kaulen et al. 2022)."""

    settingsAccepted = Signal(dict)

    def __init__(self, channel_labels, annotation_labels, has_stages=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spindle Detection (SUMO)")
        self.resize(480, 520)

        layout = QVBoxLayout(self)

        # --- EEG channel ---
        ch_group = QGroupBox("EEG channel:")
        ch_layout = QVBoxLayout()
        self._ch_list = QListWidget()
        self._ch_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._ch_list.setMaximumHeight(110)
        for name in channel_labels:
            self._ch_list.addItem(name)
        if channel_labels:
            self._ch_list.setCurrentRow(0)
        ch_layout.addWidget(self._ch_list)
        ch_group.setLayout(ch_layout)
        layout.addWidget(ch_group)

        # --- Event marker ---
        marker_group = QGroupBox("Save detections to event marker:")
        marker_layout = QVBoxLayout()
        self._marker = QComboBox()
        for label in annotation_labels:
            self._marker.addItem(label)
        if "F2" in annotation_labels:
            self._marker.setCurrentIndex(annotation_labels.index("F2"))
        marker_layout.addWidget(self._marker)
        marker_group.setLayout(marker_layout)
        layout.addWidget(marker_group)

        # --- Detection threshold ---
        thresh_group = QGroupBox("Detection threshold")
        thresh_layout = QVBoxLayout()
        thresh_layout.setSpacing(12)

        # Probability threshold
        self._prob_threshold = QDoubleSpinBox()
        self._prob_threshold.setRange(0.0, 1.0)
        self._prob_threshold.setSingleStep(0.05)
        self._prob_threshold.setDecimals(2)
        self._prob_threshold.setValue(0.5)
        thresh_layout.addRow = thresh_layout.addWidget
        thresh_layout.addWidget(
            _info_label(
                "Probability threshold:",
                "Minimum probability (0–1) for a sample to be classified as part of a spindle.\n\n"
                "Lower threshold → more detections (higher sensitivity, lower specificity)\n"
                "Higher threshold → fewer detections (lower sensitivity, higher specificity)\n\n"
                "Default: 0.5 (from Kaulen et al. 2022).",
            )
        )
        thresh_layout.addWidget(self._prob_threshold)

        thresh_group.setLayout(thresh_layout)
        layout.addWidget(thresh_group)

        # --- Stage filter ---
        self._stage_group = QGroupBox("Keep detections in sleep stages only:")
        self._stage_group.setCheckable(True)
        self._stage_group.setChecked(has_stages)
        self._stage_group.setEnabled(has_stages)

        stage_layout = QVBoxLayout()
        self._stage_checks = {}
        default_on = {"N2", "N3"}
        for stage in _STAGES:
            cb = QCheckBox(stage)
            cb.setChecked(stage in default_on)
            stage_layout.addWidget(cb)
            self._stage_checks[stage] = cb

        if not has_stages:
            note_no_stages = QLabel("No sleep stages have been scored yet.")
            note_no_stages.setStyleSheet("color: gray; font-size: 11px;")
            stage_layout.addWidget(note_no_stages)

        self._stage_group.setLayout(stage_layout)
        layout.addWidget(self._stage_group)

        # --- Info note with procedure description ---
        note_row = QWidget()
        note_layout = QHBoxLayout(note_row)
        note_layout.setContentsMargins(0, 0, 0, 0)
        note_layout.setSpacing(4)

        note = QLabel(
            "SUMO (Slim U-Net trained on MODA) detects sleep spindles using a deep neural network.\n"
            "Spindles are brief (0.5–2 s), rhythmic (11–16 Hz) bursts linked to memory consolidation.\n"
            "Based on: Kaulen et al. (2022), Sci. Rep. 12, 7686."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 11px;")
        note_layout.addWidget(note, stretch=1)

        procedure_icon = QLabel("ⓘ")
        procedure_icon.setStyleSheet("color: #5ba3d9; font-weight: bold; font-size: 13px;")
        procedure_icon.setCursor(Qt.WhatsThisCursor)
        procedure_icon.setToolTipDuration(0)
        procedure_icon.setToolTip(
            "SUMO procedure (Kaulen et al. 2022)\n"
            "─────────────────────────────────────────\n"
            "1. Pre-processing\n"
            "   The EEG signal is downsampled to 100 Hz (if needed) and\n"
            "   z-transformed (zero mean, unit variance) to normalize\n"
            "   inter-individual differences.\n"
            "\n"
            "2. U-Net inference\n"
            "   A U-Net convolutional neural network (3 levels, 16–32 filters)\n"
            "   trained on the MODA dataset processes the EEG segment.\n"
            "   Output is per-sample probability of being part of a spindle.\n"
            "\n"
            "3. Post-processing\n"
            "   Raw probabilities are smoothed with a 0.42 s moving-average\n"
            "   filter. Samples exceeding the probability threshold are\n"
            "   grouped into spindle events (start, end).\n"
            "\n"
            "4. Consensus detection\n"
            "   The model approximates expert consensus from 5+ expert\n"
            "   scorers, achieving super-human performance across ages.\n"
            "   Superior to feature-based methods (A7 algorithm)."
        )
        note_layout.addWidget(procedure_icon, alignment=Qt.AlignTop)

        layout.addWidget(note_row)

        # --- OK / Cancel ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_accept(self):
        selected = self._ch_list.currentItem()
        if selected is None:
            QMessageBox.warning(self, "No channel selected", "Please select an EEG channel.")
            return

        # Collect stage filter
        if self._stage_group.isEnabled() and self._stage_group.isChecked():
            chosen = [s for s, cb in self._stage_checks.items() if cb.isChecked()]
            if not chosen:
                QMessageBox.warning(
                    self,
                    "No stage selected",
                    "Tick at least one sleep stage, or uncheck the stage filter.",
                )
                return
            filter_stages = chosen
        else:
            filter_stages = None

        settings = {
            "channel": selected.text(),
            "marker": self._marker.currentText(),
            "prob_threshold": self._prob_threshold.value(),
            "filter_stages": filter_stages,
        }
        self.settingsAccepted.emit(settings)
        self.accept()
