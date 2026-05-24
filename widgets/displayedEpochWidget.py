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
        self.textfield.setAttribute(Qt.WA_TranslucentBackground)
        # self.textfield.setStyleSheet("QLabel { color: red; font-size: 20px; text-align: center; }")

        # Layout
        layout = QVBoxLayout(axes)
        layout.addWidget(self.textfield)

    def update_text(self, this_epoch, numepo, stages, stages_ref=None):
        stage = stages[this_epoch]["stage"]

        conf = stages[this_epoch]["confidence"]
        if conf is None:
            confidence_text = ""
        elif conf == 0:
            confidence_text = "(not sure)"
        else:
            confidence_text = f'| Confidence {np.round(conf * 100, 2)}%'

        if stages_ref is None or this_epoch >= len(stages_ref):
            self.textfield.setText(
                f'Epoch {this_epoch+1}/{numepo} | {stage} {confidence_text}'
            )
        else:
            ref_stage = stages_ref[this_epoch]["stage"]
            disagreement = stage != ref_stage
            color = "red" if disagreement else "black"
            you_span = f'<span style="color:{color};">(you: {ref_stage})</span>'
            self.textfield.setText(
                f'Epoch {this_epoch+1}/{numepo} | {stage} {you_span} {confidence_text}'
            )
    #     self.change_uncertainty(stages[this_epoch]["confidence"])

    # def change_uncertainty(self, confidence):
    #     if confidence < .5:
    #         self.textfield.setText(f"{self.textfield.text()} (not sure)")
    #     else:
    #         self.textfield.setText(self.textfield.text())
