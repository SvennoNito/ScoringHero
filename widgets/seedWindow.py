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
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QFormLayout,
)
from PySide6.QtCore import Signal


class SeedWindow(QDialog):
    settingsAccepted = Signal(dict)

    def __init__(self, channel_labels, annotation_labels, saved_paths=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("K-Complex / Spindle Detection (SEED)")
        self.resize(480, 580)
        saved_paths = saved_paths or {}

        layout = QVBoxLayout(self)

        # --- EEG channel ---
        ch_group = QGroupBox("EEG channel:")
        ch_layout = QVBoxLayout()
        self._ch_list = QListWidget()
        self._ch_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._ch_list.setMaximumHeight(120)
        for name in channel_labels:
            self._ch_list.addItem(name)
        if channel_labels:
            self._ch_list.setCurrentRow(0)
        ch_layout.addWidget(self._ch_list)
        ch_group.setLayout(ch_layout)
        layout.addWidget(ch_group)

        # --- K-complex detection ---
        self._kc_group = QGroupBox("K-complex detection")
        self._kc_group.setCheckable(True)
        self._kc_group.setChecked(True)
        kc_layout = QFormLayout()
        self._kc_marker = QComboBox()
        for label in annotation_labels:
            self._kc_marker.addItem(label)
        if "F1" in annotation_labels:
            self._kc_marker.setCurrentIndex(annotation_labels.index("F1"))
        kc_layout.addRow("Save to event marker:", self._kc_marker)
        self._kc_group.setLayout(kc_layout)
        layout.addWidget(self._kc_group)

        # --- Spindle detection ---
        self._sp_group = QGroupBox("Spindle detection")
        self._sp_group.setCheckable(True)
        self._sp_group.setChecked(False)
        sp_layout = QFormLayout()
        self._sp_marker = QComboBox()
        for label in annotation_labels:
            self._sp_marker.addItem(label)
        if "F2" in annotation_labels:
            self._sp_marker.setCurrentIndex(annotation_labels.index("F2"))
        sp_layout.addRow("Save to event marker:", self._sp_marker)
        self._sp_group.setLayout(sp_layout)
        layout.addWidget(self._sp_group)

        # --- SEED Python executable ---
        py_group = QGroupBox("SEED Python executable:")
        py_layout = QHBoxLayout()
        self._python_exe = QLineEdit(saved_paths.get("python_exe", ""))
        self._python_exe.setPlaceholderText(
            r"e.g. C:\miniconda3\envs\seed_env\python.exe"
        )
        btn_py = QPushButton("Browse")
        btn_py.clicked.connect(self._browse_python)
        py_layout.addWidget(self._python_exe)
        py_layout.addWidget(btn_py)
        py_group.setLayout(py_layout)
        layout.addWidget(py_group)

        # --- SEED repository directory ---
        dir_group = QGroupBox("SEED repository directory:")
        dir_layout = QHBoxLayout()
        self._seed_dir = QLineEdit(saved_paths.get("seed_dir", ""))
        self._seed_dir.setPlaceholderText(
            r"e.g. C:\path\to\Sleep-EEG-Event-Detector"
        )
        btn_dir = QPushButton("Browse")
        btn_dir.clicked.connect(self._browse_seed_dir)
        dir_layout.addWidget(self._seed_dir)
        dir_layout.addWidget(btn_dir)
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        note = QLabel(
            "These paths are saved automatically and will be pre-filled next time.\n"
            "SEED requires a separate conda environment with Python 3.7 and\n"
            "TensorFlow 1.15 — it cannot run inside ScoringHero's own environment."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(note)

        # --- OK / Cancel ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _browse_python(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select SEED Python executable", filter="Python (python.exe python);;All files (*)"
        )
        if path:
            self._python_exe.setText(path)

    def _browse_seed_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select SEED repository directory"
        )
        if directory:
            self._seed_dir.setText(directory)

    def _on_accept(self):
        selected = self._ch_list.currentItem()
        if selected is None:
            QMessageBox.warning(self, "No channel selected", "Please select an EEG channel.")
            return

        detect_kc = self._kc_group.isChecked()
        detect_sp = self._sp_group.isChecked()
        if not detect_kc and not detect_sp:
            QMessageBox.warning(
                self, "Nothing selected",
                "Enable K-complex detection and/or spindle detection."
            )
            return

        python_exe = self._python_exe.text().strip()
        if not python_exe:
            QMessageBox.warning(
                self, "No Python executable",
                "Please specify the path to the SEED conda environment's python.exe."
            )
            return

        settings = {
            "channel":         selected.text(),
            "detect_kc":       detect_kc,
            "kc_marker":       self._kc_marker.currentText() if detect_kc else None,
            "detect_spindles": detect_sp,
            "spindle_marker":  self._sp_marker.currentText() if detect_sp else None,
            "python_exe":      python_exe,
            "seed_dir":        self._seed_dir.text().strip(),
        }
        self.settingsAccepted.emit(settings)
        self.accept()
