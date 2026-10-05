import os

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
    QProgressDialog,
    QApplication,
    QScrollArea,
    QWidget,
)
from PySide6.QtCore import Signal, Qt

from .summaryImageWindow import SummaryImageWindow

from scoring.ezscore_env import (
    MODEL_VARIANTS,
    DEFAULT_VARIANT,
    SETUP_INSTRUCTIONS,
    create_environment,
    default_environment_dir,
    find_model_dir,
    is_model_dir,
    ezscore_importable,
)

_NO_RIGHT = "— none (duplicate the left channel) —"

# How an epoch classified as artifact by ezscore is written into the scoring
ARTIFACT_MODES = {
    "unscored":     "Leave the epoch unscored",
    "inconclusive": "Score the epoch as Inconclusive",
}


def _guess_channel(channel_labels, keywords, fallback):
    for index, name in enumerate(channel_labels):
        lowered = name.lower()
        if any(keyword in lowered for keyword in keywords):
            return index
    return fallback if fallback < len(channel_labels) else 0


class EzscoreWindow(QDialog):
    """Settings dialog for ezscore-f automatic sleep staging (Coon et al. 2025)."""

    settingsAccepted = Signal(dict)

    def __init__(self, channel_labels, annotation_labels, saved=None, app_path="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auto Score (ezscore-f)")
        self.resize(560, 720)

        saved = saved or {}
        self._channel_labels = list(channel_labels)
        self._app_path = app_path

        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        body = QWidget()
        layout = QVBoxLayout(body)
        scroll.setWidget(body)
        outer.addWidget(scroll)

        intro = QLabel(
            "ezscore-f scores two-channel <b>forehead</b> EEG (ZMax, DCM, CGX PatchEEG "
            "and comparable montages) into Wake, N1, N2, N3, REM and a sixth "
            "<b>artifact</b> class. Select the left and right forehead derivations below."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # --- Channels -----------------------------------------------------
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
            self._left.setCurrentIndex(_guess_channel(self._channel_labels, ("left", "eegl", "_l", " l"), 0))
        if right_default == _NO_RIGHT or right_default in self._channel_labels:
            self._right.setCurrentText(right_default)
        else:
            self._right.setCurrentIndex(_guess_channel(self._channel_labels, ("right", "eegr", "_r", " r"), 1))

        channel_form.addRow("Left channel (eegl):", self._left)
        channel_form.addRow("Right channel (eegr):", self._right)
        channel_group.setLayout(channel_form)
        layout.addWidget(channel_group)

        channel_note = QLabel(
            "The signals are taken as they are displayed, so any re-referencing, "
            "polarity flip or filter set in the Configuration panel is applied first."
        )
        channel_note.setWordWrap(True)
        channel_note.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(channel_note)

        # --- Model --------------------------------------------------------
        model_group = QGroupBox("Model")
        model_layout = QVBoxLayout()

        model_form = QFormLayout()
        self._model = QComboBox()
        for name, spec in MODEL_VARIANTS.items():
            self._model.addItem(spec["label"], userData=name)
        saved_variant = saved.get("variant", DEFAULT_VARIANT)
        index = self._model.findData(saved_variant)
        self._model.setCurrentIndex(index if index >= 0 else self._model.findData(DEFAULT_VARIANT))
        model_form.addRow("Variant:", self._model)
        model_layout.addLayout(model_form)

        self._model_description = QLabel()
        self._model_description.setWordWrap(True)
        self._model_description.setStyleSheet("color: gray; font-size: 11px;")
        model_layout.addWidget(self._model_description)

        dir_row = QHBoxLayout()
        self._model_dir = QLineEdit(saved.get("model_dir", ""))
        self._model_dir.setPlaceholderText("leave empty to use ~/.ezscore_models")
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

        self._model.currentIndexChanged.connect(self._refresh_model_info)
        self._model_dir.textChanged.connect(self._refresh_model_info)
        self._refresh_model_info()

        # --- Artifact class ----------------------------------------------
        artifact_group = QGroupBox("Artifact epochs")
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
            "ezscore-f is artifact-aware: epochs dominated by signal loss or movement "
            "get their own class instead of a made-up sleep stage. Keeping them "
            "unscored keeps them out of the sleep statistics."
        )
        artifact_note.setWordWrap(True)
        artifact_note.setStyleSheet("color: gray; font-size: 11px;")
        artifact_layout.addWidget(artifact_note)

        artifact_group.setLayout(artifact_layout)
        layout.addWidget(artifact_group)

        # --- Output -------------------------------------------------------
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        self._store_probs = QCheckBox(
            "Store the class probabilities (hypnodensity) in the scoring file"
        )
        self._store_probs.setChecked(bool(saved.get("store_probabilities", True)))
        output_layout.addWidget(self._store_probs)

        self._show_summary = QCheckBox(
            "Show the ezscore summary figure (hypnodensity, hypnogram, spectrograms)"
        )
        self._show_summary.setChecked(bool(saved.get("show_summary", True)))
        output_layout.addWidget(self._show_summary)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # --- Environment --------------------------------------------------
        env_group = QGroupBox("ezscore environment")
        env_layout = QVBoxLayout()

        python_row = QHBoxLayout()
        self._python_exe = QLineEdit(saved.get("python_exe", ""))
        self._python_exe.setPlaceholderText(r"e.g. C:\Postdoc\Scripts\ScoringHero\.venv_ezscore\Scripts\python.exe")
        browse_python = QPushButton("Browse")
        browse_python.clicked.connect(self._browse_python)
        python_row.addWidget(QLabel("Python executable:"))
        python_row.addWidget(self._python_exe)
        python_row.addWidget(browse_python)
        env_layout.addLayout(python_row)

        setup_row = QHBoxLayout()
        self._setup_button = QPushButton("Set up ezscore environment...")
        self._setup_button.clicked.connect(self._run_setup)
        setup_row.addWidget(self._setup_button)
        setup_row.addStretch(1)
        env_layout.addLayout(setup_row)

        env_note = QLabel(
            SETUP_INSTRUCTIONS
            if not ezscore_importable()
            else "ezscore is importable in this interpreter — leave the field empty to use it directly."
        )
        env_note.setWordWrap(True)
        env_note.setStyleSheet("color: gray; font-size: 11px;")
        env_layout.addWidget(env_note)

        env_group.setLayout(env_layout)
        layout.addWidget(env_group)
        layout.addStretch(1)

        # --- OK / Cancel ---------------------------------------------------
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        outer.addWidget(button_box)

    # -- helpers -----------------------------------------------------------

    def _current_variant(self):
        return self._model.currentData()

    def _resolved_model_dir(self):
        """Model directory to use, or None when it still has to be downloaded."""
        typed = self._model_dir.text().strip()
        variant = self._current_variant()
        if typed:
            if is_model_dir(typed):
                return typed
            nested = os.path.join(typed, variant)
            if is_model_dir(nested):
                return nested
            return None
        return find_model_dir(variant)

    def _refresh_model_info(self):
        variant = self._current_variant()
        spec = MODEL_VARIANTS.get(variant, {})
        self._model_description.setText(spec.get("description", ""))

        resolved = self._resolved_model_dir()
        if resolved:
            self._model_status.setText(f"✔ Model found: {resolved}")
            self._model_status.setStyleSheet("color: #4caf50; font-size: 11px;")
        else:
            self._model_status.setText(
                f"✖ '{variant}' not found — ScoringHero will offer to download it "
                f"(~{spec.get('size_mb', '?')} MB) when you press OK."
            )
            self._model_status.setStyleSheet("color: #e0a030; font-size: 11px;")

    def _browse_model_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select the ezscore model folder")
        if directory:
            self._model_dir.setText(directory)

    def _run_setup(self):
        """Create the sidecar environment from inside the application."""
        target = default_environment_dir(self._app_path)

        answer = QMessageBox.question(
            self,
            "Set up ezscore environment",
            "Create a Python 3.11 environment with ezscore in:\n\n"
            f"{target}\n\n"
            "This needs uv and downloads roughly 1 GB (TensorFlow). It can take "
            "several minutes.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if answer != QMessageBox.Yes:
            return

        progress = QProgressDialog("Preparing...", None, 0, 0, self)
        progress.setWindowTitle("Set up ezscore environment")
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.show()
        QApplication.processEvents()

        def on_output(line):
            progress.setLabelText(line[:200])
            QApplication.processEvents()

        self._setup_button.setEnabled(False)
        try:
            interpreter = create_environment(target, on_output=on_output)
        except Exception as exc:
            progress.close()
            QMessageBox.critical(self, "Setup failed", str(exc))
            return
        finally:
            self._setup_button.setEnabled(True)

        progress.close()
        self._python_exe.setText(interpreter)
        QMessageBox.information(
            self,
            "ezscore environment ready",
            f"ezscore is installed in:\n\n{interpreter}\n\n"
            "The model weights are downloaded when you start scoring.",
        )

    def _browse_python(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select the ezscore environment's Python executable",
            self._app_path,
            "Python (python.exe python);;All files (*)",
        )
        if path:
            self._python_exe.setText(path)

    def _on_accept(self):
        left = self._left.currentText()
        right = self._right.currentText()

        if not left:
            QMessageBox.warning(self, "No channel selected", "Please select a left forehead channel.")
            return
        if right != _NO_RIGHT and right == left:
            answer = QMessageBox.question(
                self,
                "Same channel twice",
                "Left and right channel are identical. ezscore-f expects two "
                "symmetric derivations; using one channel twice usually costs "
                "accuracy.\n\nContinue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        python_exe = self._python_exe.text().strip()
        if not python_exe and not ezscore_importable():
            QMessageBox.warning(
                self,
                "No ezscore environment",
                "ezscore cannot be imported in ScoringHero's own interpreter, so a "
                "separate one is required.\n\n" + SETUP_INSTRUCTIONS,
            )
            return

        settings = {
            "left_channel":        left,
            "right_channel":       right,
            "duplicate_left":      right == _NO_RIGHT,
            "variant":             self._current_variant(),
            "model_dir":           self._model_dir.text().strip(),
            "artifact_mode":       self._artifact_mode.currentData(),
            "mark_artifacts":      self._mark_artifacts.isChecked(),
            "artifact_marker":     self._artifact_marker.currentText(),
            "store_probabilities": self._store_probs.isChecked(),
            "show_summary":        self._show_summary.isChecked(),
            "python_exe":          python_exe,
        }
        self.settingsAccepted.emit(settings)
        self.accept()


class EzscoreSummaryWindow(SummaryImageWindow):
    """Displays the summary figure ezscore renders for a scored recording."""

    def __init__(self, image_path, parent=None):
        super().__init__(
            image_path,
            title="ezscore-f — Summary",
            caption=(
                "Top to bottom: class probabilities (hypnodensity), predicted "
                "hypnogram, and the multitaper spectrograms of both forehead "
                "channels."
            ),
            save_name="ezscore_summary.png",
            parent=parent,
        )
