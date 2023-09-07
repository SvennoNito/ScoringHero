from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider, QWidget
import numpy as np
from mouse_click import *


class SpectogramSlider(QWidget):
    def __init__(self, centralWidget):
        super().__init__()
        self.slider = QSlider(centralWidget, Qt.Vertical)
        self.slider.setValue(100)
        self.slider.setMinimum(75)
        self.slider.setFocusPolicy(Qt.NoFocus)

        # self.slider.setStyleSheet({
        #     background: #3498db;
        #     border: 1px solid #3498db;
        #     width: 8px;  /* Adjust this value to change the handle width */
        #     margin: -3px 0;
        #     border-radius: 4px;
        # })
