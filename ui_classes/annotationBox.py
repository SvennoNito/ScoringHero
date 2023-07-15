from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *

class annotationBox(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Annotation Box")
        self.layout = QVBoxLayout(self)
        self.text_field = []
        self.initUI()
               

    def initUI(self):
        plus_button = QtWidgets.QPushButton("+")
        plus_button.clicked.connect(self.add_row)

        form_layout = QFormLayout() 
        row_layout  = QHBoxLayout()
        row_layout.addWidget(plus_button)
        form_layout.addRow(row_layout)
        self.layout.addLayout(form_layout)

    def add_row(self):
        annotation_name = QLineEdit()

        color = QComboBox(self)
        color.addItem("Black")
        color.addItem("Blue")
        color.addItem("Magenta")
        color.setCurrentText(chaninfo['Color'])
        color.currentIndexChanged.connect(lambda index, chanNdx=chanNdx: self.changeColor(index, chanNdx))

        shortcut = QLineEdit()


        form_layout = QFormLayout() 
        row_layout  = QHBoxLayout()
        row_layout.addWidget(annotation_name)
        row_layout.addWidget(color)
        row_layout.addWidget(shortcut)
        form_layout.addRow(row_layout)
        self.layout.addLayout(form_layout)            


