from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
import pyqtgraph as pg
import numpy as np
from utilities import *
from signal_processing import *


class RectanglePower(QWidget):
    changesMade = Signal()

    def __init__(self, centralWidget):
        super().__init__()

        # Plot axes
        self.axes = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("RectanglePowerWidget")
        self.axes.setBackground((0, 0, 0, 0))
        self.axes.setLabel("left", "Power (unitless)")
        self.axes.setMouseEnabled(x=False, y=False)

        # bf5656
        self.pen = pg.mkPen(color="#0b1c2c", width=2)

        # Axes
        self.axes.setYRange(0, 1, padding=0)
        self.axes.getAxis('left').setTicks([])
        # self.axes.getAxis('left').setTicks([[(-4.5, "N4"), (-3.5, "N3"), (-2.5, "N2"), (-1.5, "N1"), (-0.5, "R"), (0.5, "W")]])

        # Initiate
        self.powerline = self.axes.plot([0], [0], pen=self.pen)

    def update_powerline(self, freqs, power):
        self.powerline.setData(freqs, power)
        self.axes.setXRange(freqs[0], freqs[-1], padding=0)

        """         # Get the current axis range
        axis = self.axes.getAxis('bottom')
        start, end = 5, int(freqs[-1])
        
        # Calculate reasonable tick positions (mimic PyQtGraph's auto-ticks)
        tick_positions = np.arange(start, end-5, 5, dtype=int)
        tick_count = len(tick_positions)  # Number of ticks you want

        # Create tick labels, adding "Hz" to the last one
        ticks = []
        for i, pos in enumerate(tick_positions):
            label = f"{pos:.0f}" if i < tick_count - 1 else f"Hz"
            ticks.append((pos, label))
        
        # Set the modified ticks
        axis.setTicks([ticks]) """