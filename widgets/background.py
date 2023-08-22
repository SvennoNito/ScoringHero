from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
import pyqtgraph as pg
import numpy as np

class BackgroundWidget(QWidget):
    changesMade = Signal()

    def __init__(self, centralWidget):
        super().__init__()

        # Plot axes
        self.axes = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("BackgroundWidget")
        self.axes.setBackground('w')        
        self.axes.getAxis('left').setTicks([]) 
        self.axes.getAxis('bottom').setTicks([]) 

        # Text showing current epoch
        self.textfield = QLabel(self.axes)
        self.textfield.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        font = QFont()
        font.setBold(True)
        font.Weight(75)
        self.textfield.setFont(font)
        self.textfield.setObjectName("textfield")
        self.textfield.setText("Test")
        #self.textfield.setStyleSheet("QLabel { color: red; font-size: 20px; text-align: center; }")

        # Layout
        layout = QVBoxLayout(self.axes)
        layout.addWidget(self.textfield)   

        # Pens
        self.pen_grid = pg.mkPen(color=(25, 25, 25, 15), style=Qt.DashLine) 
        self.pen_border = pg.mkPen(color=(0, 0, 0), style=Qt.DotLine, width=3) 
