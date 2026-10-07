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
    QScrollArea,
    QWidget,
)
from PySide6.QtCore import Signal

from autoscoring.nidra_env import (
    MODELS,
    DEFAULT_MODEL,
    INSTALL_INSTRUCTIONS,
    default_model_root,
    missing_model_files,
    missing_requirements,
)
from .summaryImageWindow import SummaryImageWindow

_NO_RIGHT = "— none (duplicate the left channel) —"

# How an epoch classified as artifact is written
ARTIFACT_MODES = {
    "unscored":     "Leave the epoch unscored",
    "inconclusive": "Score the epoch as Inconclusive",
}


def _looks_like(name, hints):
    lowered = name.lower()
    return any(hint in lowered for hint in hints)


def _guess_channel(channel_labels, keywords, fallback):
    """Index of the channel that most likely carries one forehead derivation.

    Non-EEG channels are searched last: a side hint like " l" matches
    "EMG L" just as well as "EEG L", and the forehead models want the EEG one.
    """
    non_eeg = ("emg", "ecg", "ekg", "eog")
    candidates = [
        index for index, name in enumerate(channel_labels)
        if not _looks_like(name, non_eeg)
    ]
    candidates += [index for index in range(len(channel_labels)) if index not in candidates]

    for index in candidates:
        if _looks_like(channel_labels[index], keywords):
            return index
    return fallback if fallback < len(channel_labels) else 0



class NidraWindow(QDialog):
    """Settings dialog for automatic sleep staging with the NIDRA ezscore-f models.

    The models are ONNX graphs run in ScoringHero's own interpreter.
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
            "NIDRA runs the validated <b>ezscore-f</b> deep-learning sleep stage "
            "classifiers for two-channel forehead EEG as ONNX models. Everything "
            "runs inside ScoringHero — no second Python environment."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # --- Channels ------------------------------------------------------
        layout.addWidget(self._build_forehead_page(saved))

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

        # --- Artifact class ------------------------------------------------
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
            "Epochs dominated by signal loss or movement get their own label "
            "instead of a made-up sleep stage. Keeping them unscored keeps them "
            "out of the sleep statistics."
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

        self._model.currentIndexChanged.connect(self._refresh_model_info)
        self._model_dir.textChanged.connect(self._refresh_model_info)

        for key, spec in MODELS.items():
            self._model.addItem(spec["label"], userData=key)
        index = self._model.findData(saved.get("model", DEFAULT_MODEL))
        self._model.setCurrentIndex(index if index >= 0 else 0)
        self._refresh_model_info()

    # -- pages -------------------------------------------------------------

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

    def _current_model(self):
        return self._model.currentData()

    def _refresh_model_info(self):
        model_key = self._current_model()
        if not model_key:
            return

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

        settings = {
            "model":               self._current_model(),
            "model_dir":           self._model_dir.text().strip(),
            "left_channel":        left,
            "right_channel":       right,
            "duplicate_left":      right == _NO_RIGHT,
            "artifact_mode":       self._artifact_mode.currentData(),
            "mark_artifacts":      self._mark_artifacts.isChecked(),
            "artifact_marker":     self._artifact_marker.currentText(),
            "store_probabilities": self._store_probs.isChecked(),
            "show_summary":        self._show_summary.isChecked(),
        }

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

