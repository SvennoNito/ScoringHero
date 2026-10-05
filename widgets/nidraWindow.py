from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QDialogButtonBox,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QStackedWidget,
    QScrollArea,
    QWidget,
)
from PySide6.QtCore import Signal, Qt

from scoring.nidra_env import (
    MODELS,
    DEFAULT_MODEL,
    INSTALL_INSTRUCTIONS,
    default_model_root,
    missing_model_files,
    missing_requirements,
    models_for_mode,
)
from .summaryImageWindow import SummaryImageWindow

_NO_RIGHT = "— none (duplicate the left channel) —"

MODES = {
    "psg":      "Full PSG — scalp EEG (± EOG)",
    "forehead": "Wearable — two-channel forehead EEG",
}

# How an epoch classified as artifact by a forehead model is written
ARTIFACT_MODES = {
    "unscored":     "Leave the epoch unscored",
    "inconclusive": "Score the epoch as Inconclusive",
}

# Channel-name fragments used to pre-select sensible defaults
_EOG_HINTS = ("eog", "loc", "roc", "e1", "e2")
_EEG_HINTS = (
    "c3", "c4", "f3", "f4", "f7", "f8", "fp1", "fp2", "o1", "o2",
    "p3", "p4", "t3", "t4", "t5", "t6", "cz", "fz", "pz",
)


def _looks_like(name, hints):
    lowered = name.lower()
    return any(hint in lowered for hint in hints)


def _guess_channel(channel_labels, keywords, fallback):
    """Index of the channel that most likely carries one forehead derivation.

    Non-EEG channels are searched last: in a full montage a side hint like
    " l" matches "EOG L" just as well as "EEG L", and the forehead models want
    the EEG one.
    """
    non_eeg = ("eog", "emg", "ecg", "ekg")
    candidates = [
        index for index, name in enumerate(channel_labels)
        if not _looks_like(name, non_eeg)
    ]
    candidates += [index for index in range(len(channel_labels)) if index not in candidates]

    for index in candidates:
        if _looks_like(channel_labels[index], keywords):
            return index
    return fallback if fallback < len(channel_labels) else 0


def _channel_list(channel_labels, preselect):
    """A multi-selection list of channel names with `preselect` checked out."""
    widget = QListWidget()
    widget.setSelectionMode(QAbstractItemView.MultiSelection)
    widget.setMaximumHeight(150)
    for name in channel_labels:
        item = QListWidgetItem(name)
        widget.addItem(item)
        if name in preselect:
            item.setSelected(True)
    return widget


class NidraWindow(QDialog):
    """Settings dialog for automatic sleep staging with the NIDRA models.

    Covers both families NIDRA ships: U-Sleep 2.0 for full polysomnography and
    the ezscore-f forehead models, all as ONNX graphs run in ScoringHero's own
    interpreter.
    """

    settingsAccepted = Signal(dict)

    def __init__(self, channel_labels, annotation_labels, saved=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auto Score (NIDRA)")
        self.resize(600, 760)

        saved = saved or {}
        self._channel_labels = list(channel_labels)

        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        body = QWidget()
        layout = QVBoxLayout(body)
        scroll.setWidget(body)
        outer.addWidget(scroll)

        intro = QLabel(
            "NIDRA runs validated deep-learning sleep stage classifiers as ONNX "
            "models: <b>U-Sleep 2.0</b> for full polysomnography and the "
            "<b>ezscore-f</b> models for two-channel forehead EEG. Everything "
            "runs inside ScoringHero — no second Python environment."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # --- Recording type ------------------------------------------------
        mode_group = QGroupBox("Recording type")
        mode_form = QFormLayout()
        self._mode = QComboBox()
        for key, label in MODES.items():
            self._mode.addItem(label, userData=key)
        index = self._mode.findData(saved.get("mode", "psg"))
        self._mode.setCurrentIndex(index if index >= 0 else 0)
        mode_form.addRow("Montage:", self._mode)
        mode_group.setLayout(mode_form)
        layout.addWidget(mode_group)

        # --- Channels ------------------------------------------------------
        self._pages = QStackedWidget()
        self._pages.addWidget(self._build_psg_page(saved))
        self._pages.addWidget(self._build_forehead_page(saved))
        layout.addWidget(self._pages)

        channel_note = QLabel(
            "The signals are taken as they are displayed, so any re-referencing, "
            "polarity flip or filter set in the Configuration panel is applied first."
        )
        channel_note.setWordWrap(True)
        channel_note.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(channel_note)

        # --- Model ---------------------------------------------------------
        model_group = QGroupBox("Model")
        model_layout = QVBoxLayout()

        model_form = QFormLayout()
        self._model = QComboBox()
        model_form.addRow("Model:", self._model)
        model_layout.addLayout(model_form)

        self._model_description = QLabel()
        self._model_description.setWordWrap(True)
        self._model_description.setStyleSheet("color: gray; font-size: 11px;")
        model_layout.addWidget(self._model_description)

        dir_row = QHBoxLayout()
        self._model_dir = QLineEdit(saved.get("model_dir", ""))
        self._model_dir.setPlaceholderText(
            f"leave empty to use {default_model_root()} or an existing NIDRA install"
        )
        browse_model = QPushButton("Browse")
        browse_model.clicked.connect(self._browse_model_dir)
        dir_row.addWidget(QLabel("Folder:"))
        dir_row.addWidget(self._model_dir)
        dir_row.addWidget(browse_model)
        model_layout.addLayout(dir_row)

        self._model_status = QLabel()
        self._model_status.setWordWrap(True)
        self._model_status.setStyleSheet("font-size: 11px;")
        model_layout.addWidget(self._model_status)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # --- Artifact class (forehead models only) --------------------------
        self._artifact_group = QGroupBox("Artifact epochs")
        artifact_layout = QVBoxLayout()

        artifact_form = QFormLayout()
        self._artifact_mode = QComboBox()
        for key, label in ARTIFACT_MODES.items():
            self._artifact_mode.addItem(label, userData=key)
        index = self._artifact_mode.findData(saved.get("artifact_mode", "unscored"))
        self._artifact_mode.setCurrentIndex(index if index >= 0 else 0)
        artifact_form.addRow("Sleep stage:", self._artifact_mode)
        artifact_layout.addLayout(artifact_form)

        marker_row = QHBoxLayout()
        self._mark_artifacts = QCheckBox("Also mark artifact epochs with event marker:")
        self._mark_artifacts.setChecked(bool(saved.get("mark_artifacts", True)))
        self._artifact_marker = QComboBox()
        self._artifact_marker.addItems(annotation_labels)
        saved_marker = saved.get("artifact_marker")
        if saved_marker in annotation_labels:
            self._artifact_marker.setCurrentText(saved_marker)
        elif "Artifact" in annotation_labels:
            self._artifact_marker.setCurrentText("Artifact")
        self._mark_artifacts.toggled.connect(self._artifact_marker.setEnabled)
        self._artifact_marker.setEnabled(self._mark_artifacts.isChecked())
        marker_row.addWidget(self._mark_artifacts)
        marker_row.addWidget(self._artifact_marker)
        marker_row.addStretch(1)
        artifact_layout.addLayout(marker_row)

        artifact_note = QLabel(
            "Only the forehead models have an artifact class: epochs dominated by "
            "signal loss or movement get their own label instead of a made-up "
            "sleep stage. Keeping them unscored keeps them out of the sleep "
            "statistics. U-Sleep always assigns one of the five sleep stages."
        )
        artifact_note.setWordWrap(True)
        artifact_note.setStyleSheet("color: gray; font-size: 11px;")
        artifact_layout.addWidget(artifact_note)

        self._artifact_group.setLayout(artifact_layout)
        layout.addWidget(self._artifact_group)

        # --- Output ---------------------------------------------------------
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        self._store_probs = QCheckBox(
            "Store the class probabilities (hypnodensity) in the scoring file"
        )
        self._store_probs.setChecked(bool(saved.get("store_probabilities", True)))
        output_layout.addWidget(self._store_probs)

        self._show_summary = QCheckBox(
            "Show a summary figure (hypnodensity and hypnogram) when scoring finishes"
        )
        self._show_summary.setChecked(bool(saved.get("show_summary", True)))
        output_layout.addWidget(self._show_summary)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # --- Requirements ----------------------------------------------------
        missing = missing_requirements()
        if missing:
            requirement_group = QGroupBox("Missing packages")
            requirement_layout = QVBoxLayout()
            requirement_note = QLabel(
                f"NIDRA scoring needs {', '.join(missing)}, which cannot be "
                "imported here.\n\n" + INSTALL_INSTRUCTIONS
            )
            requirement_note.setWordWrap(True)
            requirement_note.setStyleSheet("color: #e0a030; font-size: 11px;")
            requirement_layout.addWidget(requirement_note)
            requirement_group.setLayout(requirement_layout)
            layout.addWidget(requirement_group)

        layout.addStretch(1)

        # --- OK / Cancel ------------------------------------------------------
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        outer.addWidget(button_box)

        self._mode.currentIndexChanged.connect(self._on_mode_changed)
        self._model.currentIndexChanged.connect(self._refresh_model_info)
        self._model_dir.textChanged.connect(self._refresh_model_info)
        self._eeg_channels.itemSelectionChanged.connect(self._refresh_group_note)
        self._eog_channels.itemSelectionChanged.connect(self._refresh_group_note)

        self._saved_model = saved.get("model", DEFAULT_MODEL)
        self._on_mode_changed()
        self._refresh_group_note()

    # -- pages -------------------------------------------------------------

    def _build_psg_page(self, saved):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        default_eeg = saved.get("eeg_channels")
        if default_eeg is None:
            default_eeg = [n for n in self._channel_labels if _looks_like(n, _EEG_HINTS)]
        default_eog = saved.get("eog_channels")
        if default_eog is None:
            default_eog = [n for n in self._channel_labels if _looks_like(n, _EOG_HINTS)]

        # A channel matching both hint sets (e.g. "EOG E1-C3") belongs to EOG
        default_eeg = [n for n in default_eeg if n not in default_eog]

        channel_group = QGroupBox("Channels to score")
        channel_layout = QVBoxLayout()

        lists_row = QHBoxLayout()

        eeg_column = QVBoxLayout()
        eeg_column.addWidget(QLabel("EEG channels:"))
        self._eeg_channels = _channel_list(self._channel_labels, default_eeg)
        eeg_column.addWidget(self._eeg_channels)
        lists_row.addLayout(eeg_column)

        eog_column = QVBoxLayout()
        eog_column.addWidget(QLabel("EOG channels (optional):"))
        self._eog_channels = _channel_list(self._channel_labels, default_eog)
        eog_column.addWidget(self._eog_channels)
        lists_row.addLayout(eog_column)

        channel_layout.addLayout(lists_row)

        self._group_note = QLabel()
        self._group_note.setWordWrap(True)
        self._group_note.setStyleSheet("color: gray; font-size: 11px;")
        channel_layout.addWidget(self._group_note)

        channel_group.setLayout(channel_layout)
        page_layout.addWidget(channel_group)
        return page

    def _build_forehead_page(self, saved):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        channel_group = QGroupBox("Forehead EEG channels")
        channel_form = QFormLayout()

        self._left = QComboBox()
        self._left.addItems(self._channel_labels)
        self._right = QComboBox()
        self._right.addItems(self._channel_labels + [_NO_RIGHT])

        left_default = saved.get("left_channel")
        right_default = saved.get("right_channel")
        if left_default in self._channel_labels:
            self._left.setCurrentText(left_default)
        else:
            self._left.setCurrentIndex(
                _guess_channel(self._channel_labels, ("left", "eegl", "_l", " l"), 0)
            )
        if right_default == _NO_RIGHT or right_default in self._channel_labels:
            self._right.setCurrentText(right_default)
        else:
            self._right.setCurrentIndex(
                _guess_channel(self._channel_labels, ("right", "eegr", "_r", " r"), 1)
            )

        channel_form.addRow("Left channel (eegl):", self._left)
        channel_form.addRow("Right channel (eegr):", self._right)
        channel_group.setLayout(channel_form)
        page_layout.addWidget(channel_group)
        return page

    # -- helpers -----------------------------------------------------------

    def _current_mode(self):
        return self._mode.currentData()

    def _current_model(self):
        return self._model.currentData()

    def _selected(self, widget):
        return [item.text() for item in widget.selectedItems()]

    def _on_mode_changed(self):
        mode = self._current_mode()
        self._pages.setCurrentIndex(0 if mode == "psg" else 1)
        self._artifact_group.setVisible(mode == "forehead")

        self._model.blockSignals(True)
        self._model.clear()
        for key in models_for_mode(mode):
            self._model.addItem(MODELS[key]["label"], userData=key)
        index = self._model.findData(getattr(self, "_saved_model", DEFAULT_MODEL))
        self._model.setCurrentIndex(index if index >= 0 else 0)
        self._model.blockSignals(False)

        self._refresh_model_info()

    def _refresh_model_info(self):
        model_key = self._current_model()
        if not model_key:
            return
        self._saved_model = model_key

        spec = MODELS[model_key]
        self._model_description.setText(spec["description"])

        missing = missing_model_files(model_key, self._model_dir.text().strip())
        if not missing:
            self._model_status.setText("✔ Model weights found.")
            self._model_status.setStyleSheet("color: #4caf50; font-size: 11px;")
        else:
            self._model_status.setText(
                f"✖ {', '.join(missing)} not found — ScoringHero will offer to "
                f"download the weights (~{spec['size_mb']} MB) when you press OK."
            )
            self._model_status.setStyleSheet("color: #e0a030; font-size: 11px;")

    def _refresh_group_note(self):
        eeg = self._selected(self._eeg_channels)
        eog = self._selected(self._eog_channels)
        if not eeg:
            self._group_note.setText(
                "Select at least one EEG channel. Every EEG x EOG combination is "
                "scored separately and the class probabilities are averaged."
            )
            return

        if eog:
            groups = len(eeg) * len(eog)
            self._group_note.setText(
                f"{groups} channel group(s) — every one of the {len(eeg)} EEG "
                f"channels paired with each of the {len(eog)} EOG channels. Their "
                "class probabilities are averaged, which is what makes U-Sleep "
                "robust; more groups means proportionally longer runtime."
            )
        else:
            self._group_note.setText(
                f"{len(eeg)} channel group(s) — without an EOG channel the EEG-only "
                "U-Sleep graph is used and each EEG channel is scored on its own."
            )

    def _browse_model_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select the folder holding the NIDRA .onnx models"
        )
        if directory:
            self._model_dir.setText(directory)

    def _on_accept(self):
        missing = missing_requirements()
        if missing:
            QMessageBox.warning(
                self,
                "Missing packages",
                f"NIDRA scoring needs {', '.join(missing)}.\n\n" + INSTALL_INSTRUCTIONS,
            )
            return

        mode = self._current_mode()
        settings = {
            "mode":                mode,
            "model":               self._current_model(),
            "model_dir":           self._model_dir.text().strip(),
            "artifact_mode":       self._artifact_mode.currentData(),
            "mark_artifacts":      self._mark_artifacts.isChecked(),
            "artifact_marker":     self._artifact_marker.currentText(),
            "store_probabilities": self._store_probs.isChecked(),
            "show_summary":        self._show_summary.isChecked(),
        }

        if mode == "psg":
            eeg = self._selected(self._eeg_channels)
            eog = self._selected(self._eog_channels)
            if not eeg:
                QMessageBox.warning(
                    self,
                    "No EEG channel selected",
                    "Please select at least one EEG channel for U-Sleep.",
                )
                return
            overlap = sorted(set(eeg) & set(eog))
            if overlap:
                QMessageBox.warning(
                    self,
                    "Channel used twice",
                    "These channels are selected as both EEG and EOG:\n\n"
                    + ", ".join(overlap)
                    + "\n\nPlease assign each channel to one role only.",
                )
                return
            if len(eeg) * max(len(eog), 1) > 24:
                answer = QMessageBox.question(
                    self,
                    "Many channel groups",
                    f"{len(eeg) * max(len(eog), 1)} channel groups will be scored "
                    "one after another. That can take several minutes.\n\nContinue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if answer != QMessageBox.Yes:
                    return
            settings["eeg_channels"] = eeg
            settings["eog_channels"] = eog
        else:
            left = self._left.currentText()
            right = self._right.currentText()
            if not left:
                QMessageBox.warning(
                    self, "No channel selected", "Please select a left forehead channel."
                )
                return
            if right != _NO_RIGHT and right == left:
                answer = QMessageBox.question(
                    self,
                    "Same channel twice",
                    "Left and right channel are identical. The forehead models "
                    "expect two symmetric derivations; using one channel twice "
                    "usually costs accuracy.\n\nContinue anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if answer != QMessageBox.Yes:
                    return
            settings["left_channel"] = left
            settings["right_channel"] = right
            settings["duplicate_left"] = right == _NO_RIGHT

        self.settingsAccepted.emit(settings)
        self.accept()


class NidraSummaryWindow(SummaryImageWindow):
    """Displays the summary figure ScoringHero renders for a NIDRA scoring."""

    def __init__(self, image_path, parent=None):
        super().__init__(
            image_path,
            title="NIDRA — Summary",
            caption=(
                "Top: the class probabilities per epoch (hypnodensity) — a narrow "
                "band of one colour means a confident call, mixed colours an "
                "uncertain one. Bottom: the resulting hypnogram, with artifact "
                "epochs shaded where the model has an artifact class."
            ),
            save_name="nidra_summary.png",
            parent=parent,
        )

