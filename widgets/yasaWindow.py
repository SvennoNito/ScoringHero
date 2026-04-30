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


class YasaWindow(QDialog):
    """Settings dialog for YASA spindle detection (Vallat et al.)."""

    settingsAccepted = Signal(dict)

    def __init__(self, channel_labels, annotation_labels, has_stages=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spindle Detection (YASA)")
        self.resize(480, 680)

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
        if "F2" in annotation_labels:
            self._marker.setCurrentIndex(annotation_labels.index("F2"))
        marker_layout.addRow("Event marker:", self._marker)
        marker_group.setLayout(marker_layout)
        layout.addWidget(marker_group)

        # --- Detection thresholds ---
        thresh_group = QGroupBox("Detection thresholds")
        thresh_layout = QFormLayout()
        thresh_layout.setLabelAlignment(Qt.AlignLeft)

        # Relative power
        self._rel_pow = QDoubleSpinBox()
        self._rel_pow.setRange(0.0, 1.0)
        self._rel_pow.setSingleStep(0.05)
        self._rel_pow.setDecimals(2)
        self._rel_pow.setValue(0.2)
        thresh_layout.addRow(
            _info_label(
                "Relative power (rel_pow):",
                "Minimum relative power: power ratio of spindle band (freq_sp)\n"
                "to broad band (freq_broad).\n\n"
                "Default: 0.2\n"
                "Higher values = more conservative detection.",
            ),
            self._rel_pow,
        )

        # Correlation
        self._corr = QDoubleSpinBox()
        self._corr.setRange(0.0, 1.0)
        self._corr.setSingleStep(0.05)
        self._corr.setDecimals(2)
        self._corr.setValue(0.65)
        thresh_layout.addRow(
            _info_label(
                "Correlation (corr):",
                "Minimum correlation between original and sigma-filtered signal.\n\n"
                "Default: 0.65\n"
                "Higher values = more conservative detection.",
            ),
            self._corr,
        )

        # RMS threshold
        self._rms = QDoubleSpinBox()
        self._rms.setRange(0.0, 10.0)
        self._rms.setSingleStep(0.1)
        self._rms.setDecimals(1)
        self._rms.setValue(1.5)
        self._rms.setSuffix(" σ")
        thresh_layout.addRow(
            _info_label(
                "RMS threshold (rms):",
                "Number of standard deviations above the mean of moving RMS\n"
                "of sigma-filtered signal.\n\n"
                "Default: 1.5\n"
                "Higher values = more conservative detection.",
            ),
            self._rms,
        )

        # Min. duration
        self._min_dur = QDoubleSpinBox()
        self._min_dur.setRange(0.1, 5.0)
        self._min_dur.setSingleStep(0.1)
        self._min_dur.setDecimals(1)
        self._min_dur.setValue(0.5)
        self._min_dur.setSuffix(" s")
        thresh_layout.addRow(
            _info_label(
                "Min. duration (min_dur):",
                "Minimum allowed spindle duration.\n\n"
                "Default: 0.5 s",
            ),
            self._min_dur,
        )

        # Max. duration
        self._max_dur = QDoubleSpinBox()
        self._max_dur.setRange(1.0, 10.0)
        self._max_dur.setSingleStep(0.1)
        self._max_dur.setDecimals(1)
        self._max_dur.setValue(2.0)
        self._max_dur.setSuffix(" s")
        thresh_layout.addRow(
            _info_label(
                "Max. duration (max_dur):",
                "Maximum allowed spindle duration.\n\n"
                "Default: 2.0 s",
            ),
            self._max_dur,
        )

        # --- Frequency band ---
        freq_group = QGroupBox("Frequency bands")
        freq_layout = QFormLayout()

        # Spindle band low
        self._freq_sp_low = QDoubleSpinBox()
        self._freq_sp_low.setRange(1.0, 20.0)
        self._freq_sp_low.setSingleStep(0.5)
        self._freq_sp_low.setDecimals(1)
        self._freq_sp_low.setValue(12.0)
        self._freq_sp_low.setSuffix(" Hz")
        freq_layout.addRow(
            _info_label(
                "Spindle band low (freq_sp):",
                "Lower frequency bound of spindle detection band.\n\n"
                "Default: 12 Hz",
            ),
            self._freq_sp_low,
        )

        # Spindle band high
        self._freq_sp_high = QDoubleSpinBox()
        self._freq_sp_high.setRange(1.0, 20.0)
        self._freq_sp_high.setSingleStep(0.5)
        self._freq_sp_high.setDecimals(1)
        self._freq_sp_high.setValue(15.0)
        self._freq_sp_high.setSuffix(" Hz")
        freq_layout.addRow(
            _info_label(
                "Spindle band high (freq_sp):",
                "Upper frequency bound of spindle detection band.\n\n"
                "Default: 15 Hz",
            ),
            self._freq_sp_high,
        )

        # Broad band low
        self._freq_broad_low = QDoubleSpinBox()
        self._freq_broad_low.setRange(0.5, 10.0)
        self._freq_broad_low.setSingleStep(0.5)
        self._freq_broad_low.setDecimals(1)
        self._freq_broad_low.setValue(1.0)
        self._freq_broad_low.setSuffix(" Hz")
        freq_layout.addRow(
            _info_label(
                "Broad band low (freq_broad):",
                "Lower frequency bound of broad band (for relative power).\n\n"
                "Default: 1 Hz",
            ),
            self._freq_broad_low,
        )

        # Broad band high
        self._freq_broad_high = QDoubleSpinBox()
        self._freq_broad_high.setRange(10.0, 50.0)
        self._freq_broad_high.setSingleStep(1.0)
        self._freq_broad_high.setDecimals(1)
        self._freq_broad_high.setValue(30.0)
        self._freq_broad_high.setSuffix(" Hz")
        freq_layout.addRow(
            _info_label(
                "Broad band high (freq_broad):",
                "Upper frequency bound of broad band (for relative power).\n\n"
                "Default: 30 Hz",
            ),
            self._freq_broad_high,
        )

        freq_group.setLayout(freq_layout)
        thresh_group.setLayout(thresh_layout)
        layout.addWidget(thresh_group)
        layout.addWidget(freq_group)

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
        note = QLabel(
            "YASA detects sleep spindles via spectral analysis and correlation.\n"
            "Based on: Vallat et al., Frontiers in Neuroinformatics 15, 576073 (2021)."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(note)

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

        # Validate frequency bands
        if self._freq_sp_low.value() >= self._freq_sp_high.value():
            QMessageBox.warning(
                self,
                "Invalid frequency band",
                "Spindle band low must be less than spindle band high.",
            )
            return

        if self._freq_broad_low.value() >= self._freq_broad_high.value():
            QMessageBox.warning(
                self,
                "Invalid frequency band",
                "Broad band low must be less than broad band high.",
            )
            return

        # Validate durations
        if self._min_dur.value() >= self._max_dur.value():
            QMessageBox.warning(
                self,
                "Invalid duration",
                "Min. duration must be less than max. duration.",
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
            "rel_pow":       self._rel_pow.value(),
            "corr":          self._corr.value(),
            "rms":           self._rms.value(),
            "min_dur":       self._min_dur.value(),
            "max_dur":       self._max_dur.value(),
            "freq_sp":       (self._freq_sp_low.value(), self._freq_sp_high.value()),
            "freq_broad":    (self._freq_broad_low.value(), self._freq_broad_high.value()),
            "filter_stages": filter_stages,
        }
        self.settingsAccepted.emit(settings)
        self.accept()
