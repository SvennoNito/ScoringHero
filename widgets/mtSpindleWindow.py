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
    QSpinBox,
    QFormLayout,
    QMessageBox,
    QWidget,
    QCheckBox,
)
from PySide6.QtCore import Signal, Qt

_STAGES = ["Wake", "N1", "N2", "N3", "REM", "Inconclusive"]


def _info_label(text, tooltip):
    """Return a QWidget with a field label and a hoverable info icon."""
    widget = QWidget()
    row = QHBoxLayout(widget)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(5)

    row.addWidget(QLabel(text))

    icon = QLabel("i")
    icon.setStyleSheet("color: #5ba3d9; font-weight: bold;")
    icon.setToolTip(tooltip)
    icon.setToolTipDuration(0)
    icon.setCursor(Qt.WhatsThisCursor)
    row.addWidget(icon)
    row.addStretch()

    return widget


class MtSpindleWindow(QDialog):
    """Settings dialog for MT-Spindle spindle detection."""

    settingsAccepted = Signal(dict)

    def __init__(self, channel_labels, annotation_labels, has_stages=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spindle Detection (MT-Spindle)")
        self.resize(440, 600)

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
        marker_layout = QFormLayout()
        self._marker = QComboBox()
        for label in annotation_labels:
            self._marker.addItem(label)
        if "F3" in annotation_labels:
            self._marker.setCurrentIndex(annotation_labels.index("F3"))
        marker_layout.addRow("Event marker:", self._marker)
        marker_group.setLayout(marker_layout)
        layout.addWidget(marker_group)

        # --- Detection thresholds ---
        thresh_group = QGroupBox("Detection thresholds")
        thresh_layout = QFormLayout()
        thresh_layout.setLabelAlignment(Qt.AlignLeft)

        # Min. frequency
        self._fmin = QDoubleSpinBox()
        self._fmin.setRange(8.0, 14.0)
        self._fmin.setSingleStep(0.5)
        self._fmin.setDecimals(1)
        self._fmin.setValue(11.0)
        self._fmin.setSuffix(" Hz")
        thresh_layout.addRow(
            _info_label(
                "Min. spindle frequency (fmin):",
                "Lower bound (Hz) of the spindle frequency band.\n\n"
                "Sleep spindles occur at 12-16 Hz (sigma band).\n"
                "Default: 11 Hz (includes slower spindles).",
            ),
            self._fmin,
        )

        # Max. frequency
        self._fmax = QDoubleSpinBox()
        self._fmax.setRange(14.0, 18.0)
        self._fmax.setSingleStep(0.5)
        self._fmax.setDecimals(1)
        self._fmax.setValue(16.0)
        self._fmax.setSuffix(" Hz")
        thresh_layout.addRow(
            _info_label(
                "Max. spindle frequency (fmax):",
                "Upper bound (Hz) of the spindle frequency band.\n\n"
                "Standard sigma band: 12-16 Hz.\n"
                "Default: 16 Hz.",
            ),
            self._fmax,
        )

        # Min. amplitude (µV envelope)
        self._amin = QDoubleSpinBox()
        self._amin.setRange(1.0, 100.0)
        self._amin.setSingleStep(1.0)
        self._amin.setDecimals(1)
        self._amin.setValue(10.0)
        self._amin.setSuffix(" µV")
        thresh_layout.addRow(
            _info_label(
                "Min. amplitude (Amin):",
                "Minimum peak envelope amplitude (µV) of the\n"
                "sigma-band filtered signal within a spindle.\n\n"
                "Lower values are more sensitive (more detections).\n"
                "Typical spindle envelope: 10–30 µV.\n"
                "Default: 10.0 µV.",
            ),
            self._amin,
        )

        # Min. duration
        self._dmin = QDoubleSpinBox()
        self._dmin.setRange(0.3, 1.0)
        self._dmin.setSingleStep(0.1)
        self._dmin.setDecimals(1)
        self._dmin.setValue(0.5)
        self._dmin.setSuffix(" s")
        thresh_layout.addRow(
            _info_label(
                "Min. duration (Dmin):",
                "Minimum allowed duration of a spindle.\n\n"
                "Sleep spindles typically last 0.5-2.0 seconds.\n"
                "Default: 0.5 s.",
            ),
            self._dmin,
        )

        # Max. duration
        self._dmax = QDoubleSpinBox()
        self._dmax.setRange(1.0, 3.0)
        self._dmax.setSingleStep(0.5)
        self._dmax.setDecimals(1)
        self._dmax.setValue(2.0)
        self._dmax.setSuffix(" s")
        thresh_layout.addRow(
            _info_label(
                "Max. duration (Dmax):",
                "Maximum allowed duration of a spindle.\n\n"
                "Candidate waveforms longer than this are discarded.\n"
                "Default: 2.0 s.",
            ),
            self._dmax,
        )

        # Candidate-region percentile
        self._q = QSpinBox()
        self._q.setRange(50, 99)
        self._q.setSingleStep(1)
        self._q.setValue(95)
        self._q.setSuffix(" %")
        thresh_layout.addRow(
            _info_label(
                "Candidate region percentile (q):",
                "Controls selectivity when identifying time regions\n"
                "that may contain a spindle candidate.\n\n"
                "Higher q -> fewer candidate regions -> fewer\n"
                "(but more confident) detections.\n"
                "Default: 90.",
            ),
            self._q,
        )

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

        # --- Info note ---
        note_row = QWidget()
        note_layout = QHBoxLayout(note_row)
        note_layout.setContentsMargins(0, 0, 0, 0)
        note_layout.setSpacing(4)

        note = QLabel(
            "MT-Spindle detects spindles via multitaper spectral analysis.\n"
            "Adapted from MT-KCD (Oliveira et al. 2020) for sigma-band (12-16 Hz).\n"
            "Runs in-process — no external dependencies required."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 11px;")
        note_layout.addWidget(note, stretch=1)

        procedure_icon = QLabel("i")
        procedure_icon.setStyleSheet("color: #5ba3d9; font-weight: bold; font-size: 13px;")
        procedure_icon.setCursor(Qt.WhatsThisCursor)
        procedure_icon.setToolTipDuration(0)
        procedure_icon.setToolTip(
            "MT-Spindle procedure\n"
            "─────────────────────────────────────────\n"
            "1. Broadband bandpass filter (0.3–35 Hz)\n"
            "\n"
            "2. Multitaper spectrogram\n"
            "   (same as MT-KCD)\n"
            "\n"
            "3. Candidate region identification\n"
            "   Median-normalized sigma-band power;\n"
            "   percentile threshold q (same as MT-KCD)\n"
            "\n"
            "4. Sigma-band envelope via Hilbert transform\n"
            "   (bandpass fmin–fmax Hz)\n"
            "\n"
            "5. Spindle boundary detection\n"
            "   envelope > local background within region\n"
            "\n"
            "6. Duration & amplitude filter\n"
            "   dmin ≤ duration < dmax AND peak ≥ amin"
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

        # Frequency band validation
        if self._fmin.value() >= self._fmax.value():
            QMessageBox.warning(
                self,
                "Invalid frequency band",
                "Minimum frequency must be less than maximum frequency.",
            )
            return

        # Duration validation
        if self._dmin.value() >= self._dmax.value():
            QMessageBox.warning(
                self,
                "Invalid duration range",
                "Minimum duration must be less than maximum duration.",
            )
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
            "channel":       selected.text(),
            "marker":        self._marker.currentText(),
            "fmin":          self._fmin.value(),
            "fmax":          self._fmax.value(),
            "amin":          self._amin.value(),
            "dmin_s":        self._dmin.value(),
            "dmax_s":        self._dmax.value(),
            "q":             float(self._q.value()),
            "filter_stages": filter_stages,
        }
        self.settingsAccepted.emit(settings)
        self.accept()
