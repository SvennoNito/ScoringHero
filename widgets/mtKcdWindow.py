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


class MtKcdWindow(QDialog):
    """Settings dialog for MT-KCD K-complex detection (Oliveira et al. 2020)."""

    settingsAccepted = Signal(dict)

    def __init__(self, channel_labels, annotation_labels, has_stages=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("K-Complex Detection (MT-KCD)")
        self.resize(440, 580)

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
        if "F1" in annotation_labels:
            self._marker.setCurrentIndex(annotation_labels.index("F1"))
        marker_layout.addRow("Event marker:", self._marker)
        marker_group.setLayout(marker_layout)
        layout.addWidget(marker_group)

        # --- Detection thresholds ---
        thresh_group = QGroupBox("Detection thresholds")
        thresh_layout = QFormLayout()
        thresh_layout.setLabelAlignment(Qt.AlignLeft)

        # Min. amplitude
        self._amin = QDoubleSpinBox()
        self._amin.setRange(1.0, 500.0)
        self._amin.setSingleStep(5.0)
        self._amin.setDecimals(1)
        self._amin.setValue(75.0)
        self._amin.setSuffix(" µV")
        thresh_layout.addRow(
            _info_label(
                "Min. amplitude (Amin):",
                "Minimum peak-to-peak amplitude a waveform must have to be\n"
                "accepted as a K-complex.\n\n"
                "The AASM standard requires ≥ 75 µV.\n"
                "Increasing this makes detection more conservative\n"
                "(fewer but more prominent KCs).",
            ),
            self._amin,
        )

        # Max. duration
        self._dmax = QDoubleSpinBox()
        self._dmax.setRange(0.5, 10.0)
        self._dmax.setSingleStep(0.5)
        self._dmax.setDecimals(1)
        self._dmax.setValue(2.0)
        self._dmax.setSuffix(" s")
        thresh_layout.addRow(
            _info_label(
                "Max. duration (Dmax):",
                "Maximum allowed duration of a K-complex.\n\n"
                "Candidate waveforms longer than this are discarded —\n"
                "very long slow waves are more likely to be delta activity\n"
                "than true KCs.\n\n"
                "AASM default: 2 s.",
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
                "Controls how selective the algorithm is when identifying\n"
                "time regions that contain a KC candidate.\n\n"
                "The multitaper spectrogram delta-band power is smoothed\n"
                "at two timescales (short vs. background). Regions where the\n"
                "short-term average exceeds the background by more than the\n"
                "q-th percentile of all differences are flagged as candidates.\n\n"
                "Higher q → fewer candidate regions → fewer (but more\n"
                "confident) detections.\n"
                "Default: 95 (from Oliveira et al. 2020, Table 1).",
            ),
            self._q,
        )

        # Max. KC frequency
        self._fmax = QDoubleSpinBox()
        self._fmax.setRange(1.0, 6.0)
        self._fmax.setSingleStep(0.5)
        self._fmax.setDecimals(1)
        self._fmax.setValue(3.0)
        self._fmax.setSuffix(" Hz")
        thresh_layout.addRow(
            _info_label(
                "Max. KC frequency (fmax):",
                "Upper frequency bound (Hz) of the delta-band power\n"
                "concentration used to identify KC candidates in the\n"
                "multitaper spectrogram.\n\n"
                "KCs appear as power bursts in roughly 0–3 Hz.\n"
                "Prerau et al. (2017) note that KC spectral power\n"
                "attenuates sharply by 2–3 Hz.\n\n"
                "Default: 3 Hz.",
            ),
            self._fmax,
        )

        thresh_group.setLayout(thresh_layout)
        layout.addWidget(thresh_group)

        # --- Stage filter ---
        self._stage_group = QGroupBox("Keep detections in sleep stages only:")
        self._stage_group.setCheckable(True)
        self._stage_group.setChecked(has_stages)  # on by default when stages exist
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
            "MT-KCD detects KCs via multitaper spectral analysis.\n"
            "Runs in-process — no external dependencies required.\n"
            "Based on: Oliveira et al. (2020), Expert Syst. Appl. 151, 113331."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 11px;")
        note_layout.addWidget(note, stretch=1)

        procedure_icon = QLabel("ⓘ")
        procedure_icon.setStyleSheet("color: #5ba3d9; font-weight: bold; font-size: 13px;")
        procedure_icon.setCursor(Qt.WhatsThisCursor)
        procedure_icon.setToolTipDuration(0)
        procedure_icon.setToolTip(
            "MT-KCD procedure (Oliveira et al. 2020)\n"
            "─────────────────────────────────────────\n"
            "1. Pre-processing\n"
            "   The EEG signal is bandpass-filtered (0.3–35 Hz) to\n"
            "   suppress low- and high-frequency artefacts.\n"
            "\n"
            "2. Multitaper spectrogram\n"
            "   A spectrogram is computed using multiple DPSS tapers\n"
            "   (K = 3 at default settings). Averaging K single-taper\n"
            "   estimates reduces both bias and variance compared to a\n"
            "   standard periodogram spectrogram, giving cleaner\n"
            "   time-frequency resolution.\n"
            "\n"
            "3. Candidate region identification\n"
            "   The summed delta-band power (0–fmax Hz) is extracted\n"
            "   per spectrogram column. A short-term moving average is\n"
            "   compared to a longer background average; columns where\n"
            "   the difference exceeds the q-th percentile are grouped\n"
            "   into candidate regions.\n"
            "\n"
            "4. Candidate KC marking\n"
            "   Within each candidate region, waveforms whose smoothed\n"
            "   amplitude dips below and rises above a time-varying\n"
            "   background band (±1 SD) are marked as KC candidates.\n"
            "\n"
            "5. Candidates elimination\n"
            "   Per region, only the waveform with the highest\n"
            "   peak-to-peak amplitude is retained. It is then accepted\n"
            "   only if its amplitude ≥ Amin and duration ≤ Dmax."
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
            filter_stages = None   # no filtering

        settings = {
            "channel":       selected.text(),
            "marker":        self._marker.currentText(),
            "amin":          self._amin.value(),
            "dmax_s":        self._dmax.value(),
            "q":             float(self._q.value()),
            "fmax":          self._fmax.value(),
            "filter_stages": filter_stages,
        }
        self.settingsAccepted.emit(settings)
        self.accept()
