from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QDialogButtonBox,
    QGroupBox,
    QScrollArea,
    QWidget,
    QMessageBox,
)
from PySide6.QtCore import Signal


class GsscWindow(QDialog):
    settingsAccepted = Signal(dict)

    def __init__(self, channel_labels, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auto Score (GSSC)")
        self.resize(400, 450)

        layout = QVBoxLayout(self)

        # --- EEG channels (optional) ---
        eeg_group = QGroupBox("EEG channels (optional):")
        eeg_layout = QVBoxLayout()

        eeg_scroll = QScrollArea()
        eeg_scroll.setWidgetResizable(True)
        eeg_scroll_widget = QWidget()
        eeg_scroll_inner = QVBoxLayout(eeg_scroll_widget)

        self._eeg_checkboxes = []
        for name in channel_labels:
            cb = QCheckBox(name)
            self._eeg_checkboxes.append(cb)
            eeg_scroll_inner.addWidget(cb)
        eeg_scroll_inner.addStretch(1)

        eeg_scroll.setWidget(eeg_scroll_widget)
        eeg_layout.addWidget(eeg_scroll)
        eeg_group.setLayout(eeg_layout)
        layout.addWidget(eeg_group)

        # --- EOG channels (optional) ---
        eog_group = QGroupBox("EOG channels (optional):")
        eog_layout = QVBoxLayout()

        eog_scroll = QScrollArea()
        eog_scroll.setWidgetResizable(True)
        eog_scroll_widget = QWidget()
        eog_scroll_inner = QVBoxLayout(eog_scroll_widget)

        self._eog_checkboxes = []
        for name in channel_labels:
            cb = QCheckBox(name)
            self._eog_checkboxes.append(cb)
            eog_scroll_inner.addWidget(cb)
        eog_scroll_inner.addStretch(1)

        eog_scroll.setWidget(eog_scroll_widget)
        eog_layout.addWidget(eog_scroll)
        eog_group.setLayout(eog_layout)
        layout.addWidget(eog_group)

        # --- Filter checkbox ---
        self.filter_checkbox = QCheckBox("Apply GSSC internal filters (0.3\u201330 Hz)")
        self.filter_checkbox.setChecked(True)
        layout.addWidget(self.filter_checkbox)

        # --- OK / Cancel ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_accept(self):
        eeg_channels = [cb.text() for cb in self._eeg_checkboxes if cb.isChecked()]
        eog_channels = [cb.text() for cb in self._eog_checkboxes if cb.isChecked()]

        if not eeg_channels and not eog_channels:
            QMessageBox.warning(
                self,
                "No channels selected",
                "Please select at least one EEG or EOG channel.",
            )
            return

        settings = {
            "eeg": eeg_channels,
            "eog": eog_channels,
            "filter": self.filter_checkbox.isChecked(),
        }
        self.settingsAccepted.emit(settings)
        self.accept()
