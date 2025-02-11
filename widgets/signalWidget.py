from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsRectItem
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor, QBrush, QPen
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

        self.x_unit_format = {
            "Seconds": {"format": "{:.0f} s", "div": 1},
            "Minutes": {"format": "{:.2f} min", "div": 60},
            "Hours": {"format": "{:.3f} h", "div": 3600},
        }        

        self.pen_amplines = pg.mkPen(color=(0, 0, 0, 80), style=Qt.DotLine)
        self.pen_border = pg.mkPen(color=(0, 0, 0), style=Qt.DashLine, width=5)
        self.pen_grid_1s = pg.mkPen(color=(25, 25, 25, 15), style=Qt.DashLine)
        self.pen_grid = pg.mkPen(color=(100, 149, 237), style=Qt.DotLine)
        self.transparent_numbers = pg.mkPen(color=(255, 255, 255, 0))

        # Create a pen with a custom dash pattern
        self.penCustomDash = pg.mkPen(color=(0, 0, 0, 80), width=1)
        self.penCustomDash.setStyle(Qt.CustomDashLine)
        self.penCustomDash.setDashPattern([10, 30])  # Example: 10 pixels dash, 5 pixels gap


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
            # amplitude_line = pg.InfiniteLine(
            #     angle=0,
            #     pos=0
            #     - config[0]["Distance_between_channels_muV"] * numchans_visible * chan_counter
            #     + config[1][visible_counter]["Vertical_shift"]
            #     + 0 * config[1][visible_counter]["Scaling_factor"] / 100,
            #     pen=self.pen_amplines,
            # )
            # self.axes.addItem(amplitude_line)

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
            - 40 - 12*numchans_visible,
            + 40 + 12*numchans_visible,
            padding=0,
        )

        # Add grid lines using pg.GridItem
        grid_item = pg.GridItem()
        grid_item.setTickSpacing(x=[1], y=[config[0]["Distance_between_channels_muV"] * numchans_visible if numchans_visible > 1 else 10000])  # This could be a problem if you have few channels
        grid_item.setTextPen(self.transparent_numbers)
        self.axes.addItem(grid_item)

        # Epoch border grid
        #grid_item = pg.GridItem()
        #grid_item.setTickSpacing(x=[borders[1] - borders[0]], y=[1])
        #grid_item.setTextPen(self.transparent_numbers)
        #grid_item.setPen(self.pen_border)
        #self.axes.addItem(grid_item)
        self.axes.showGrid(x=True, y=False)     

        # Darker areas on both sides
        bottom, top     = self.axes.viewRange()[1]
        color           = QColor(0, 0, 0, 35)
        brush           = QBrush(color)    
        no_pen          = QPen(Qt.NoPen)    
        self.dark_area  = [ QGraphicsRectItem(times[0], top, config[0]["Extension_epoch_s"][0] if this_epoch > 0 else 0, bottom-top),
                            QGraphicsRectItem(borders[1], top, config[0]["Extension_epoch_s"][1] if this_epoch < len(times_and_indices)-1 else 0, bottom-top) ]
        for iarea in range(len(self.dark_area)):
            self.dark_area[iarea].setBrush(brush)
            self.dark_area[iarea].setPen(no_pen)
            self.axes.addItem(self.dark_area[iarea])

        # Show artefacts
        # self.changesMade.emit()

        # Rectangle shape text
        self.text_period = pg.TextItem(text="", color=(10, 100, 10), anchor=(0.1, 0.2))
        font = QFont()
        font.setPixelSize(12)
        self.text_period.setFont(font)
        self.axes.addItem(self.text_period)

        self.text_amplitude_box = pg.TextItem(text="", color=(10, 100, 10), anchor=(0.1, 0.9))
        font = QFont()
        font.setPixelSize(12)
        self.text_amplitude_box.setFont(font)
        self.text_amplitude_box.setRotation(270)        
        self.axes.addItem(self.text_amplitude_box)

        self.text_amplitude_signal = pg.TextItem(text="", color=(10, 100, 10), anchor=(0.1, 0.9))
        font = QFont()
        font.setPixelSize(12)
        self.text_amplitude_signal.setFont(font)
        self.axes.addItem(self.text_amplitude_signal)    

        # Thicker vertical line in the middle
        self.divide_center_line(borders)               

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
        borders = times_and_indices[this_epoch][2]

        # Thicker vertical line in the middle
        self.divide_center_line(borders)        

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

        # Adjust dark areas
        bottom, top  = self.axes.viewRange()[1]
        self.dark_area[0].setRect(times[0], top, config[0]["Extension_epoch_s"][0] if this_epoch > 0 else 0, bottom-top)
        self.dark_area[1].setRect(borders[1], top, config[0]["Extension_epoch_s"][1] if this_epoch < len(times_and_indices)-1 else 0, bottom-top)

    def adjust_time_axis(self, config, times):

        # Determine the format string based on the unit
        unit_format = self.x_unit_format[config[0]["EEG_panel_time_unit"]]

        # Generate the tick labels using list comprehension
        ticklabels = [
            (tick, unit_format["format"].format(tick / unit_format["div"]))
            for tick in np.round(np.arange(0, times[-1], config[0]["Epoch_length_s"] / 5), 1)
        ]
         
        self.axes.getAxis("bottom").setTicks([ticklabels])
        self.axes.setXRange(times[0], times[-1], padding=0)

    def divide_center_line(self, borders):

        # Thicker vertical line in the middle
        center_time = (borders[0] + borders[1]) / 2
        center_line = pg.InfiniteLine(
            pos=center_time,
            angle=90,
            pen=self.penCustomDash
        )
        self.axes.addItem(center_line)              