from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider, QWidget
import numpy as np
from mouse_click import *


class HypnogramSlider(QWidget):
    def __init__(self, centralWidget):
        super().__init__()
        self.slider = QSlider(centralWidget, Qt.Vertical)
        self.slider.setValue(100)
        self.slider.setMinimum(0)      
        self.slider.setMaximum(100)      
        self.slider.setFocusPolicy(Qt.NoFocus)

        self.slider.sliderMoved.connect(self.transform_value)  

    def transform_value(self, value):
        remainder       = value % 2
        value_by_two    = value - remainder if remainder < 1 else value + (2 - remainder)
        self.slider.setValue(value_by_two)                

        # self.slider.setStyleSheet({
        #     background: #3498db;
        #     border: 1px solid #3498db;
        #     width: 8px;  /* Adjust this value to change the handle width */
        #     margin: -3px 0;
        #     border-radius: 4px;
        # })
