from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
import numpy as np


class DisplayedEpochWidget(QWidget):
    changesMade = Signal()

    def __init__(self, axes):
        super().__init__()

        self.textfield = QLabel(axes)
        self.textfield.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        font = QFont()
        font.setBold(True)
        font.Weight(75)
        self.textfield.setFont(font)
        self.textfield.setObjectName("textfield")
        self.textfield.setText("Epoch 1 | Stage ?")
        # self.textfield.setStyleSheet("QLabel { color: red; font-size: 20px; text-align: center; }")

        # Layout
        layout = QVBoxLayout(axes)
        layout.addWidget(self.textfield)

    def update_text(self, this_epoch, numepo, stages):
        self.textfield.setText(f'Epoch {this_epoch+1}/{numepo} | {stages[this_epoch]["stage"]}')

    def change_uncertainty(self, uncertainty):
        if uncertainty == 1:
            self.textfield.setText(f'{self.textfield.text()} (not sure)')
        else:
            self.textfield.setText(self.textfield.text()[:-10])