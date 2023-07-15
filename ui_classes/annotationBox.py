from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *

class annotationBox(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Annotation Box")
        self.layout = QVBoxLayout(self)
        self.text_field = []
        self.form_layout = []
        self.initUI()
               

    def initUI(self):
        plus_button = QtWidgets.QPushButton("+")
        plus_button.clicked.connect(self.add_row)
        minus_button = QtWidgets.QPushButton("-")
        minus_button.clicked.connect(self.remove_row)

        form_layout = QFormLayout() 
        row_layout  = QHBoxLayout()
        row_layout.addWidget(plus_button)
        row_layout.addWidget(minus_button)
        form_layout.addRow(row_layout)
        self.layout.addLayout(form_layout)

    def add_row(self):
        annotation_name = QLineEdit()
        annotation_name.setText("Label")

        colorRGB = QLineEdit()
        colorRGB.setText("(0, 0, 0)")
        
        shortcut = QLabel()
        shortcut.setText(f'Ctrl+{self.layout.count()}')

        form_layout = QFormLayout() 
        row_layout  = QHBoxLayout()
        row_layout.addWidget(annotation_name)
        row_layout.addWidget(colorRGB)
        row_layout.addWidget(shortcut)
        form_layout.addRow(row_layout)
        self.layout.addLayout(form_layout)
        self.form_layout = form_layout       

    def remove_row(self):
        if self.layout.count() > 1:
            item = self.layout.takeAt(self.layout.count() - 1)
            if item:
                layout_item = item.layout()
                if layout_item:
                    while layout_item.count():
                        layout_item.removeAt(0)
                    self.layout.removeItem(item)
                    # Delete the item to free up memory
                    del item


