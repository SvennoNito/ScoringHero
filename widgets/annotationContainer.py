
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui, QtCore
from PyQt5.QtCore import QObject, pyqtSignal


class AnnotationContainer(QObject):
    changesMade = pyqtSignal()
    def __init__(self, colorindex=0, label='Artefact', parent=None):
        super().__init__(parent)

        self.colorpalette = [
            (255, 200, 200, 100), 
            (44, 160, 44, 100),
            (31, 119, 180, 100),
            (255, 127, 14, 100),
            (214, 39, 40, 100),
            (148, 103, 189, 100),
            (140, 86, 75, 100),
            (227, 119, 194, 100),
            (127, 127, 127, 100),
            (188, 189, 34, 100),
        ]

        self.facecolor      = self.colorpalette[colorindex]
        self.label          = label if not (label=="F0") else "Artifact"
        self.borders        = []
        self.drawn_boxes    = []
        self.epochs         = []
