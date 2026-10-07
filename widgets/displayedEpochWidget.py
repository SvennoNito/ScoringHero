from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from utilities.epoch_header import epoch_header_text


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
        self.textfield.setAttribute(Qt.WA_TranslucentBackground)
        # self.textfield.setStyleSheet("QLabel { color: red; font-size: 20px; text-align: center; }")

        # Layout
        layout = QVBoxLayout(axes)
        layout.addWidget(self.textfield)

    def update_text(self, this_epoch, numepo, scoring, scoring_comparison=None, comparison_name=None):
        self.textfield.setText(
            epoch_header_text(this_epoch, numepo, scoring, scoring_comparison, comparison_name)
        )
    #     self.change_uncertainty(stages[this_epoch]["confidence"])

    # def change_uncertainty(self, confidence):
    #     if confidence < .5:
    #         self.textfield.setText(f"{self.textfield.text()} (not sure)")
    #     else:
    #         self.textfield.setText(self.textfield.text())
