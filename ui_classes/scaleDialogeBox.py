from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *

class scaleDialogeBox(QtWidgets.QDialog):
    changesMade = QtCore.pyqtSignal()

    def __init__(self, chaninfos, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.chaninfo = chaninfos
        self.scale      = []
        self.display    = []
        self.color      = []

        # Loop through channels
        for count, chaninfo in enumerate(self.chaninfo):

            # Channe label
            labelbox = QLabel(chaninfo['Channel'])
            labelbox.setAlignment(QtCore.Qt.AlignRight)
            labelbox.setFixedWidth(max(len(chaninfo['Channel']) for chaninfo in self.chaninfo)*8)

            # Value by which EEG is multiplied
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setValue(chaninfo['Scale'])
            spinbox.valueChanged.connect(self.emit_signal)  

            # Whether channel is displayed or not
            checkbox = QCheckBox(self)
            checkbox.setChecked(chaninfo['Display']) 
            checkbox.clicked.connect(self.emit_signal)

            # Channel color
            colorbox = QComboBox(self)
            colorbox.addItem("Black")
            colorbox.addItem("Blue")
            colorbox.addItem("Magenta")
            colorbox.setCurrentText(chaninfo['Color'])
            colorbox.currentIndexChanged.connect(self.emit_signal)

            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(spinbox)
            row_layout.addWidget(colorbox)
            form_layout.addRow(row_layout)

            self.scale.append(spinbox) # append  
            self.display.append(checkbox)
            self.color.append(colorbox)

        layout.addLayout(form_layout)

    def emit_signal(self):
        for counter, chaninfo in enumerate(self.chaninfo):
            chaninfo['Color']   = self.color[counter].currentText()
            chaninfo['Display'] = self.display[counter].isChecked()
            chaninfo['Scale']   = self.scale[counter].value()
        self.changesMade.emit()

    
