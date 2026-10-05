from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


class SummaryImageWindow(QDialog):
    """Scaled viewer for a summary figure an auto scorer rendered to PNG.

    Shared by the classifier dialogs so every scorer presents its figure the
    same way: fitted to the window width, with a caption and a save button.
    """

    def __init__(
        self,
        image_path,
        title="Summary",
        caption="",
        save_name="summary.png",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._pixmap = QPixmap(image_path)
        self._save_name = save_name

        layout = QVBoxLayout(self)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignCenter)
        self._scroll.setWidget(self._label)
        layout.addWidget(self._scroll)

        if caption:
            caption_label = QLabel(caption)
            caption_label.setWordWrap(True)
            caption_label.setStyleSheet("color: gray; font-size: 11px;")
            layout.addWidget(caption_label)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        save_button = QPushButton("Save figure as...")
        save_button.clicked.connect(lambda: self._save(image_path))
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_row.addWidget(save_button)
        button_row.addWidget(close_button)
        layout.addLayout(button_row)

        self.resize(1100, 620)
        self._rescale()

    def _rescale(self):
        if self._pixmap.isNull():
            self._label.setText("The summary figure could not be loaded.")
            return
        width = max(320, self._scroll.viewport().width() - 2)
        self._label.setPixmap(
            self._pixmap.scaledToWidth(width, Qt.SmoothTransformation)
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale()

    def _save(self, image_path):
        target, _ = QFileDialog.getSaveFileName(
            self, "Save summary figure", self._save_name, "PNG image (*.png)"
        )
        if not target:
            return
        try:
            import shutil
            shutil.copyfile(image_path, target)
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Could not save the figure:\n\n{exc}")
