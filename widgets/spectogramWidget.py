from PyQt5 import QtWidgets, QtGui
import pyqtgraph as pg
import numpy as np
from scipy.signal import welch, find_peaks


class SpectogramWidget(QtWidgets.QWidget):
    def __init__(self, centralWidget):
        # Spectogram widget
        pg.setConfigOptions(imageAxisOrder="row-major")
        self.graphics = pg.GraphicsLayoutWidget(centralWidget)
        self.graphics.setObjectName("spectogram")
        self.graphics.setBackground("w")
        self.axes = self.graphics.addPlot()

    def draw_spectogram(self, power, freqs, freqsOI, config):
        power = np.log10(power)[:, freqsOI]
        freqs = freqs[freqsOI]
        times = np.arange(0, power.shape[0]) * config[0]["Epoch_length_s"] / 60 / 60

        # https://github.com/epeters13/pyqtspecgram/blob/main/src/pyqtspecgram/pyqtspecgram.py
        pg.setConfigOptions(imageAxisOrder="col-major")
        self.img = pg.ImageItem()
        self.img.setImage(power)
        self.img.setColorMap(pg.colormap.get("cividis"))
        self.img.setLevels(
            [-1, np.nanpercentile(power, 97)]
        )  # Color scale      np.nanpercentile(power, 0)

        self.axes.clear()
        self.axes.addItem(self.img)
        self.axes.setLimits(xMin=0, xMax=len(times), yMin=0, yMax=len(freqs))
        # self.axes.setLabel('bottom', "Time", units='min')
        self.axes.setLabel("left", "Freq", units="Hz", **{})  # 'font-size':'20px'

        self.axes.setXRange(0, len(times), padding=0)
        self.axes.setYRange(0, len(freqs), padding=0)

        # y ticks
        freqres = np.unique(np.diff(freqs))[0]
        desired_tick_values = np.arange(0, max(freqs), 5)
        index_of_desired_tick_values_in_freqs = np.unique(
            [(np.abs(freqs - tick_value)).argmin() for tick_value in desired_tick_values]
        )
        desired_tick_string = list(
            map(str, [int(y) for y in index_of_desired_tick_values_in_freqs * freqres])
        )
        desired_tick_tuple = [
            (val, text)
            for val, text in zip(index_of_desired_tick_values_in_freqs, desired_tick_string)
        ]
        self.axes.getAxis("left").setTicks([desired_tick_tuple, []])

        # xticks
        timeres = np.unique(np.diff(times))[0]
        desired_tick_values = np.round(np.arange(0, max(times), 1), 1)
        index_of_desired_tick_values_in_times = np.unique(
            [(np.abs(times - tick_value)).argmin() for tick_value in desired_tick_values]
        )
        desired_tick_string = list(
            map(
                str,
                [
                    int(x)
                    for x in desired_tick_values[0 : len(index_of_desired_tick_values_in_times)]
                ],
            )
        )
        desired_tick_tuple = [
            (val, f"{text} h")
            for val, text in zip(index_of_desired_tick_values_in_times, desired_tick_string)
        ]
        self.axes.getAxis("bottom").setTicks([desired_tick_tuple, []])

        # Initialize epoch indicator line
        self.epoch_indicator_line = pg.InfiniteLine(
            pos=1 - 0.5, angle=90, pen=pg.mkPen(color="w", width=1.8)
        )
        self.axes.addItem(self.epoch_indicator_line)

    def update_epoch_indicator(self, this_epoch):
        self.epoch_indicator_line.setPos(this_epoch + 0.5)

    def adjust_color_limit(self, power, upper_limit):
        self.img.setLevels([-1, np.nanpercentile(np.log10(power), upper_limit)])

    def coordinates_upon_mousclick(self, event):
        mouse_pos = self.graphics.mapFromScene(event.scenePos())
        image_pos = self.axes.mapFromParent(mouse_pos)
        mouse_click_coordinates = self.axes.mapToView(image_pos)
        x_axis_range = self.axes.getViewBox().viewRange()[0]
        if (
            mouse_click_coordinates.x() >= x_axis_range[0]
            and mouse_click_coordinates.x() < x_axis_range[1]
        ):
            return np.floor(mouse_click_coordinates.x()).astype(int)
