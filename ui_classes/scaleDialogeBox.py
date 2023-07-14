from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *

class scaleDialogeBox(QtWidgets.QDialog):
    def __init__(self, scales, checkticks, channelcolor, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.scaling_spinboxes      = []
        self.displayChannels        = []
        self.channelColors    = []

        # Loop through channels
        for chanNdx, (scale, checks, chancolor) in enumerate(zip(scales, checkticks, channelcolor)):
            label = QLabel(f"Channel {chanNdx+1}")
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            #spinbox.setMaximum(100)
            spinbox.setValue(scale)

            checkbox = QCheckBox(self)
            checkbox.setChecked(checks)  # Checkbox initially checked   

            #color_box = QColorDialog(self)
            #color_button = QPushButton('Choose Color', self)
            #color_button.clicked.connect(lambda checked, color_box=color_box, chanNdx=chanNdx: self.changeColor(color_box, chanNdx))
            color_combo = QComboBox(self)
            color_combo.addItem("Black")
            color_combo.addItem("Blue")
            color_combo.addItem("Magenta")
            color_combo.setCurrentText(chancolor)
            color_combo.currentIndexChanged.connect(lambda index, chanNdx=chanNdx: self.changeColor(index, chanNdx))


            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(label)
            row_layout.addWidget(spinbox)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(color_combo)
            form_layout.addRow(row_layout)

            self.scaling_spinboxes.append(spinbox) # append  
            self.displayChannels.append(checkbox)
            self.channelColors.append('Black')

        layout.addLayout(form_layout)

    def changeColor(self, index, chanNdx):
        color_mapping = {0: "Black", 1: "Blue", 2: "Magenta"}
        self.channelColors[chanNdx] = color_mapping[index]      