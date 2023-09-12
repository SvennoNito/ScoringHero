from PySide6.QtCore import Qt, QRect, Signal, QPoint
from PySide6.QtWidgets import QSlider, QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPainter, QBrush, QColor, QFont

import pyqtgraph as pg
import numpy as np


class PaintEventWidget(QWidget):
    changesMade = Signal()

    def __init__(self):
        super().__init__()
        self.brush = QBrush(QColor(10, 100, 10, 40))
        self.reset()
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.rect_limits = self.rect()

        # Create a label to display the totalLength value
        self.length_text = QLabel(self)
        font = QFont()
        font.setBold(True)
        font.setWeight(QFont.Bold)
        self.length_text.setFont(font)
        self.length_text.setObjectName("totalLengthLabel")
        self.length_text.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.length_text.setText(f"Total Length: 0.00 s")
        self.length_text.setAttribute(Qt.WA_TranslucentBackground)

        # Use QVBoxLayout for relative positioning
        layout = QVBoxLayout(self)
        layout.addWidget(self.length_text)

    def mousePressEvent(self, event):
        self.store_new_rectangle(event)

    def mouseMoveEvent(self, event):
        self.update_last_rectangle(event)
        self.update()

    def mouseReleaseEvent(self, event):
        self.update_last_rectangle(event)
        self.changesMade.emit()
        self.update_text_label()
        self.update()

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setBrush(self.brush)
        for corners in self.stored_corners:
            width = corners[1].x() - corners[0].x()
            height = corners[1].y() - corners[0].y()
            qp.drawRect(QRect(corners[0].x(), corners[0].y(), width, height))
            # for line, width, height in zip(self.stored_corners, self.width, self.height):

    def resizeEvent(self, event):
        self.rect_limits = self.rect()

    def store_new_rectangle(self, event):
        self.stored_corners.append([event.pos(), event.pos()])
        # self.width.append([])
        # self.height.append([])

    def update_last_rectangle(self, event):
        self.stored_corners[-1][1] = event.pos()
        self.respect_boder()

    def respect_boder(self):
        if self.stored_corners[-1][1].y() < self.rect_limits.top():
            self.stored_corners[-1][1].setY(self.rect_limits.top())

    def update_text_label(self):
        total_length = sum(
            [abs(corners[1].x() - corners[0].x()) for corners in self.stored_corners]
        )
        # self.length_text.setText(f"Total Length: {round(total_length, 2)} s")

    def reset(self):
        self.stored_corners = []
        self.changesMade.emit()
        self.update()

        # self.width          = []
        # self.height         = []
