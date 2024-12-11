import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui, QtCore
from PySide6.QtCore import QObject, Signal


class AnnotationContainer(QObject):
    changesMade = Signal()

    def __init__(self, colorindex=0, label="Artefact", parent=None):
        super().__init__(parent)

        self.colorpalette = [
            (255, 200, 200, 75),
            (100, 149, 237, 100),
            (152, 251, 152, 100),
            (255, 255, 102, 100),
            (64, 224, 208, 100),
            (148, 103, 189, 100),
            (140, 86, 75, 100),
            (227, 119, 194, 100),
            (127, 127, 127, 100),
            (188, 189, 34, 100),
            (255, 165, 0, 100),
            (75, 0, 130, 100),
            (255, 105, 180, 100)            
        ]

        self.facecolor = self.colorpalette[colorindex]
        self.key = label if not (label == "F0") else "A"
        # self.label = f"Event {label[-1]}" if not (label == "F0") else "Artifact (A)"
        self.label = f"{label}" if not (label == "F0") else "Artifact"
        self.borders = []
        self.drawn_boxes = []
        self.epochs = []
