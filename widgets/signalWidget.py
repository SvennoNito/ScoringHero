from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
import pyqtgraph as pg
import numpy as np
from utilities.timing_decorator import timing_decorator
from signal_processing import *


class SignalWidget(QWidget):
    changesMade = Signal()

    def __init__(self, centralWidget):
        super().__init__()

        # Plot axes
        self.axes = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("SignalWidget")
        self.axes.setBackground((0, 0, 0, 0))
        self.axes.getAxis("left").setTicks([])
        self.axes.showGrid(x=True, y=True, alpha=1)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)

        self.channelColorPalette = {
            "Black": (0, 0, 0),
            "Blue": (100, 149, 237),
            "Magenta": (233, 30, 99),
            "Green": (0, 128, 64),
        }

        self.pen_amplines = pg.mkPen(color=(0, 0, 0, 80), style=Qt.DotLine)
        self.pen_border = pg.mkPen(color=(0, 0, 0), style=Qt.DashLine, width=5)
        self.pen_grid_1s = pg.mkPen(color=(25, 25, 25, 15), style=Qt.DashLine)
        self.pen_grid = pg.mkPen(color=(100, 149, 237), style=Qt.DotLine)

    @timing_decorator
    def draw_signal(self, config, eeg_data, times_and_indices, this_epoch):
        # Indices of visible channels
        index_visible_chans = [
            counter for counter, info in enumerate(config[1]) if info["Display_on_screen"]
        ]
        numchans_visible = len(index_visible_chans)

        ## Extract times vector
        times = times_and_indices[this_epoch][0]
        index_times = times_and_indices[this_epoch][1]
        borders = times_and_indices[this_epoch][2]

        # Initiate list
        self.drawn_signals = []
        self.written_channel_labels  = []

        # Loop through channels
        self.axes.clear()
        for chan_counter, visible_counter in enumerate(index_visible_chans):
            pen = pg.mkPen(
                color=self.channelColorPalette[config[1][visible_counter]["Channel_color"]]
            )

            # Extract data
            data = eeg_data[visible_counter][index_times]

            # Plot EEG
            drawn_signal = self.axes.plot(
                times,
                data * config[1][visible_counter]["Scaling_factor"] / 100
                + config[1][visible_counter]["Vertical_shift"]
                - config[0]["Distance_between_channels_muV"] * numchans_visible * chan_counter,
                pen=pen,
            )
            self.drawn_signals.append(drawn_signal)

            # Amplitude lines
            amplitude_line = pg.InfiniteLine(
                angle=0,
                pos=0
                - config[0]["Distance_between_channels_muV"] * numchans_visible * chan_counter
                + config[1][visible_counter]["Vertical_shift"]
                + 37.5 * config[1][visible_counter]["Scaling_factor"] / 100,
                pen=self.pen_amplines,
            )
            self.axes.addItem(amplitude_line)
            amplitude_line = pg.InfiniteLine(
                angle=0,
                pos=0
                - config[0]["Distance_between_channels_muV"] * numchans_visible * chan_counter
                + config[1][visible_counter]["Vertical_shift"]
                - 37.5 * config[1][visible_counter]["Scaling_factor"] / 100,
                pen=self.pen_amplines,
            )
            self.axes.addItem(amplitude_line)
            amplitude_line = pg.InfiniteLine(
                angle=0,
                pos=0
                - config[0]["Distance_between_channels_muV"] * numchans_visible * chan_counter
                + config[1][visible_counter]["Vertical_shift"]
                + 0 * config[1][visible_counter]["Scaling_factor"] / 100,
                pen=self.pen_amplines,
            )
            self.axes.addItem(amplitude_line)

            # Add +37.5 muV text on the first channel
            if chan_counter == 0 and this_epoch == 1:
                text1 = pg.TextItem(text="+37.5 \u03BCV", color=(150, 150, 150), anchor=(0, 0.5))
                text2 = pg.TextItem(text="-37.5 \u03BCV", color=(150, 150, 150), anchor=(0, 0.5))
                text1.setPos(
                    times[0],
                    0
                    - config[0]["Distance_between_channels_muV"]
                    + config[1][visible_counter]["Vertical_shift"]
                    * numchans_visible
                    * chan_counter
                    + 37.5 * config[1][visible_counter]["Scaling_factor"] / 100,
                )
                text2.setPos(
                    times[0],
                    0
                    - config[0]["Distance_between_channels_muV"]
                    + config[1][visible_counter]["Vertical_shift"]
                    * numchans_visible
                    * chan_counter
                    - 37.5 * config[1][visible_counter]["Scaling_factor"] / 100,
                )
                font = QFont()
                font.setPixelSize(18)
                text1.setFont(font)
                text2.setFont(font)
                self.axes.addItem(text1)
                self.axes.addItem(text2)

            # Add channel labels
            channel_label = pg.TextItem(
                text=config[1][visible_counter]["Channel_name"],
                color=(150, 150, 150),
                anchor=(0, 0.5),
            )
            channel_label.setPos(
                times[0],
                0 - config[0]["Distance_between_channels_muV"] * numchans_visible * chan_counter,
            )
            font = QFont()
            font.setPixelSize(20)
            channel_label.setFont(font)
            self.axes.addItem(channel_label)
            self.written_channel_labels.append(channel_label)

        # Draw background and adjust axes
        self.adjust_time_axis(config, times)
        self.axes.setYRange(
            -config[0]["Distance_between_channels_muV"]
            * (chan_counter)
            * (numchans_visible)
            - 50,
            + 50,
            padding=0,
        )

        # Add grid lines using pg.GridItem
        grid_item = pg.GridItem()
        grid_item.setTickSpacing(x=[1], y=[1])  # This could be a problem if you have few channels
        self.axes.addItem(grid_item)

        # Epoch border grid
        grid_item = pg.GridItem()
        grid_item.setTickSpacing(x=[borders[1] - borders[0]], y=[1])
        grid_item.setPen(self.pen_border)
        self.axes.addItem(grid_item)

        # Show artefacts
        # self.changesMade.emit()

        # Rectangle shape text
        self.text_period = pg.TextItem(text="", color=(10, 100, 10), anchor=(0, 0.75))
        font = QFont()
        font.setPixelSize(12)
        self.text_period.setFont(font)
        self.axes.addItem(self.text_period)
        self.text_amplitude = pg.TextItem(text="", color=(10, 100, 10), anchor=(0.1, 0.9))
        font = QFont()
        font.setPixelSize(12)
        self.text_amplitude.setFont(font)
        self.axes.addItem(self.text_amplitude)

    @timing_decorator
    def update_signal(self, config, eeg_data, times_and_indices, this_epoch):
        # Indices of visible channels
        index_visible_chans = [
            counter for counter, info in enumerate(config[1]) if info["Display_on_screen"]
        ]
        numchans_visible = len(index_visible_chans)

        # Extract times and indices
        times = times_and_indices[this_epoch][0]
        index_times = times_and_indices[this_epoch][1]

        for chan_counter, visible_counter in enumerate(index_visible_chans):
            pen = pg.mkPen(
                color=self.channelColorPalette[config[1][visible_counter]["Channel_color"]]
            )

            # Extract data
            data = eeg_data[visible_counter][index_times]

            # Update signal
            self.drawn_signals[chan_counter].setData(
                times,
                data * config[1][visible_counter]["Scaling_factor"] / 100
                + config[1][visible_counter]["Vertical_shift"]
                - config[0]["Distance_between_channels_muV"] * numchans_visible * chan_counter,
                pen=pen,
            )

            # Update position of label
            self.written_channel_labels[chan_counter].setPos(
                times[0],
                0 - config[0]["Distance_between_channels_muV"] * numchans_visible * chan_counter,
            )

        # Draw background and adjust axes
        self.adjust_time_axis(config, times)

    def adjust_time_axis(self, config, times):
        ticklabels = [
            (tick, f"{int(tick)} s")
            for tick in np.round(np.arange(0, times[-1], config[0]["Epoch_length_s"] / 5), 1)
        ]
        self.axes.getAxis("bottom").setTicks([ticklabels])
        self.axes.setXRange(times[0], times[-1], padding=0)
