from style.plot_style import soften_axes
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from .channelPill import ChannelPill
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
        soften_axes(self.axes)
        self.axes.setObjectName("RectanglePowerWidget")
        self.axes.setBackground((0, 0, 0, 0))
        self.axes.setLabel("left", "Power (unitless)")
        self.axes.setMouseEnabled(x=False, y=False)

        # Channel name pill in the top-left corner; this panel is narrow, so its pill may
        # take more than the usual quarter of the width
        self.channel_pill = ChannelPill(self.axes, corner=True, max_fraction=0.6)
        self.channel_pill.setParentItem(self.axes.getViewBox())
        self.axes.getViewBox().sigResized.connect(self.channel_pill.refresh)

        # bf5656
        self.pen = pg.mkPen(color="#0b1c2c", width=2)

        # Axes
        self.axes.setYRange(0, 1, padding=0)
        self.axes.getAxis('left').setTicks([])
        self.axes.showGrid(x=True, y=False, alpha=0.3)

        # Initiate
        self.powerline = self.axes.plot([0], [0], pen=self.pen)

    def update_powerline(self, freqs, power, channel_name=""):
        self.powerline.setData(freqs, power)
        self.axes.setXRange(freqs[0], freqs[-1], padding=0)
        self.channel_pill.set_name(channel_name)

        # Build x ticks with "Hz" suffix on the last label
        step = 5 if freqs[-1] <= 30 else 10
        tick_positions = np.arange(
            np.ceil(freqs[0] / step) * step, freqs[-1] + 1e-6, step, dtype=float
        )
        ticks = [
            (pos, f"{int(pos)} Hz" if i == len(tick_positions) - 1 else f"{int(pos)}")
            for i, pos in enumerate(tick_positions)
        ]
        self.axes.getAxis('bottom').setTicks([ticks, []])