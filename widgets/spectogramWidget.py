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
        self.adjust_time_axis(config, times)

        # Initialize epoch indicator line
        self.epoch_indicator_line = pg.InfiniteLine(
            pos=1 - 0.5, angle=90, pen=pg.mkPen(color="w", width=1.8)
        )
        self.axes.addItem(self.epoch_indicator_line)

    def adjust_time_axis(self, config, times):
        # xticks

        if times[-1] >= 4:
            # every 60 minutes
            desired_tick_values = np.round(np.arange(0, max(times), 1/60*60), 4)
            unit_format = {'format': '{:.0f}h', 'mult': 1}
        elif times[-1] >= 2:
            # every 30 minutes
            desired_tick_values = np.round(np.arange(0, max(times), 1/60*30), 4)
            unit_format = {'format': '{:.1f}h', 'mult': 1}
        elif times[-1] >= 1:
            # every 15 minutes
            desired_tick_values = np.round(np.arange(0, max(times), 1/60*15), 4)
            unit_format = {'format': '{:.0f}m', 'mult': 60}
        elif times[-1]*60 > 45:
            # every 10 minutes
            desired_tick_values = np.round(np.arange(0, max(times), 1/60*10), 4)
            unit_format = {'format': '{:.0f}m', 'mult': 60}            
        elif times[-1]*60 > 30:
            # every 5 minutes
            desired_tick_values = np.round(np.arange(0, max(times), 1/60*5), 4)
            unit_format = {'format': '{:.0f}m', 'mult': 60}
        elif times[-1]*60 > 18:
            # every 3 minutes
            desired_tick_values = np.round(np.arange(0, max(times), 1/60*3), 4)
            unit_format = {'format': '{:.0f}m', 'mult': 60}
        elif times[-1]*60 > 10:
            # every 2 minutes
            desired_tick_values = np.round(np.arange(0, max(times), 1/60*2), 4)
            unit_format = {'format': '{:.0f}m', 'mult': 60}            
        else:
            # every minute
            desired_tick_values = np.round(np.arange(0, max(times), 1/60), 4)
            unit_format = {'format': '{:.0f}m', 'mult': 60}


        index_of_desired_tick_values_in_times = np.unique(
            [(np.abs(times - tick_value)).argmin() for tick_value in desired_tick_values]
        )
       
        ticklabels = [
            (tick, unit_format["format"].format(label * unit_format["mult"]))
            for tick, label in zip(index_of_desired_tick_values_in_times, desired_tick_values)
        ]

        # Remove .0
        ticklabels = [(hour, label.replace('.0', '')) for hour, label in ticklabels]

        self.axes.getAxis("bottom").setTicks([ticklabels, []])        

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
