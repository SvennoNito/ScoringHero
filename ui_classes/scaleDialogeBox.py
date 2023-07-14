from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *

class scaleDialogeBox(QtWidgets.QDialog):
    changesMade = QtCore.pyqtSignal()

    def __init__(self, chaninfos, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.chaninfos = chaninfos

        # Loop through channels
        for chanNdx, chaninfo in enumerate(chaninfos):
            label = QLabel(f"Channel {chanNdx+1}")
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            #spinbox.setMaximum(100)
            spinbox.setValue(chaninfo['Scale'])
            spinbox.valueChanged.connect(self.emit_signal)  # Connect the valueChanged signal of the spin box to the spinBoxValueChanged method


            checkbox = QCheckBox(self)
            checkbox.setChecked(chaninfo['Display'])  # Checkbox initially checked   
            checkbox.clicked.connect(self.emit_signal)  # Connect the checkbox clicked signal to the checkboxClicked method

            #color_box = QColorDialog(self)
            #color_button = QPushButton('Choose Color', self)
            #color_button.clicked.connect(lambda checked, color_box=color_box, chanNdx=chanNdx: self.changeColor(color_box, chanNdx))
            color_combo = QComboBox(self)
            color_combo.addItem("Black")
            color_combo.addItem("Blue")
            color_combo.addItem("Magenta")
            color_combo.setCurrentText(chaninfo['Color'])
            color_combo.currentIndexChanged.connect(lambda index, chanNdx=chanNdx: self.changeColor(index, chanNdx))

            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(label)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(spinbox)
            row_layout.addWidget(color_combo)
            form_layout.addRow(row_layout)

            #self.scaling_spinboxes.append(spinbox) # append  
            #self.displayChannels.append(checkbox)
            #self.channelColors.append('Black')

        layout.addLayout(form_layout)

    def changeColor(self, index, chanNdx):
        color_mapping = {0: "Black", 1: "Blue", 2: "Magenta"}
        self.chaninfos[chanNdx]['Color'] = color_mapping[index]     
        self.emit_signal()

    def emit_signal(self):
        self.changesMade.emit()

    
