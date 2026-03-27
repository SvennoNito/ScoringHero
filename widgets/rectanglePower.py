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

        # Channel name label (overlaid on top of the plot)
        self._channel_label = QLabel(self.axes)
        self._channel_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        font = QFont()
        font.setBold(True)
        self._channel_label.setFont(font)
        self._channel_label.setAttribute(Qt.WA_TranslucentBackground)
        self._channel_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._channel_label.setStyleSheet("color: black;")
        self._channel_label.setObjectName("periodogram_channel_label")
        channel_layout = QVBoxLayout(self.axes)
        channel_layout.addWidget(self._channel_label)

        # bf5656
        self.pen = pg.mkPen(color="#0b1c2c", width=2)

        # Axes
        self.axes.setYRange(0, 1, padding=0)
        self.axes.getAxis('left').setTicks([])
        # self.axes.getAxis('left').setTicks([[(-4.5, "N4"), (-3.5, "N3"), (-2.5, "N2"), (-1.5, "N1"), (-0.5, "R"), (0.5, "W")]])

        # Initiate
        self.powerline = self.axes.plot([0], [0], pen=self.pen)

    def update_powerline(self, freqs, power, channel_name=""):
        self.powerline.setData(freqs, power)
        self.axes.setXRange(freqs[0], freqs[-1], padding=0)
        self._channel_label.setText(channel_name)

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