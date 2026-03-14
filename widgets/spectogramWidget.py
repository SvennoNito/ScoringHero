import os
from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import pyqtgraph as pg
import numpy as np
from scipy.signal import welch, find_peaks


class SpectogramWidget(QtWidgets.QWidget):
    def __init__(self, centralWidget, app_path):
        # Spectogram widget
        pg.setConfigOptions(imageAxisOrder="row-major")
        self.graphics = pg.GraphicsLayoutWidget(centralWidget)
        self.graphics.setObjectName("spectogram")
        self.graphics.setBackground("w")
        self.axes = self.graphics.addPlot()

        self._channel_label = QLabel(self.graphics)
        self._channel_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        font = QFont()
        font.setBold(True)
        self._channel_label.setFont(font)
        self._channel_label.setAttribute(Qt.WA_TranslucentBackground)
        self._channel_label.setStyleSheet("color: white;")
        self._channel_label.setObjectName("spectogram_channel_label")
        channel_layout = QVBoxLayout(self.graphics)
        channel_layout.addWidget(self._channel_label)
        self._colormap = self._load_colormap(app_path)

        # Colorbar text labels (created once; _cbar_img is recreated per draw)
        self._cbar_min_label = pg.TextItem(color=(0, 0, 0), anchor=(0.5, 0))
        self._cbar_max_label = pg.TextItem(color=(255, 255, 255), anchor=(0.5, 1))
        self._cbar_min_label.setZValue(11)
        self._cbar_max_label.setZValue(11)
        self._cbar_img = None

    @staticmethod
    def _load_colormap(app_path):
        colormap_path = os.path.join(app_path, "spectral.txt")
        rgb = np.loadtxt(colormap_path)
        rgba = np.hstack([
            (rgb * 255).clip(0, 255).astype(np.uint8),
            np.full((len(rgb), 1), 255, dtype=np.uint8),
        ])
        positions = np.linspace(0.0, 1.0, len(rgb))
        return pg.ColorMap(positions, rgba)

    def draw_spectogram(self, power, freqs, freqsOI, config):
        power = np.log10(power)[:, freqsOI]
        freqs = freqs[freqsOI]
        times = np.arange(0, power.shape[0]) * config[0]["Epoch_length_s"] / 60 / 60
        levels = config[0].get("Spectrogram_power_limits", [-1, 3])

        # https://github.com/epeters13/pyqtspecgram/blob/main/src/pyqtspecgram/pyqtspecgram.py
        pg.setConfigOptions(imageAxisOrder="col-major")
        colormap = pg.colormap.get("cividis")
        self.img = pg.ImageItem()
        self.img.setImage(power)
        self.img.setColorMap(colormap)
        self.img.setLevels(levels)

        # Recreate colorbar ImageItem here so it inherits the current col-major setting
        self._cbar_img = pg.ImageItem()
        self._cbar_img.setColorMap(colormap)
        self._cbar_img.setZValue(10)

        self.axes.clear()
        self.axes.addItem(self.img)
        self.axes.addItem(self._cbar_img)
        self.axes.addItem(self._cbar_min_label)
        self.axes.addItem(self._cbar_max_label)
        self.axes.setLimits(xMin=0, xMax=len(times), yMin=0, yMax=len(freqs))
        # self.axes.setLabel('bottom', "Time", units='min')
        self.axes.setLabel("left", "")

        self.axes.setXRange(0, len(times), padding=0)
        self.axes.setYRange(0, len(freqs), padding=0)

        # y ticks - adaptive based on frequency range (mirrors TFWidget linear logic)
        lo, hi = freqs[0], freqs[-1]
        if hi <= 30:
            step = 5
        elif hi <= 60:
            step = 10
        else:
            step = 20
        first_tick = np.ceil(lo / step) * step if lo > 0 else 0.0
        desired_hz = [f for f in np.arange(first_tick, hi + 1e-6, step) if lo <= f <= hi + 1e-6]
        freq_ticks = [
            (int(np.argmin(np.abs(freqs - hz))), f"{int(round(hz))} Hz")
            for hz in desired_hz
        ]
        self.axes.getAxis("left").setTicks([freq_ticks, []])

        # xticks
        self.adjust_time_axis(config, times)

        # Channel label
        channel_label = config[0].get("Channel_for_spectogram", "")
        self._channel_label.setText(channel_label)

        # Colorbar
        n_times = power.shape[0]
        n_freqs = power.shape[1]
        cbar_width = max(1, int(n_times * 0.012))
        cbar_margin = n_freqs * 0.15
        cbar_y = cbar_margin
        cbar_height = n_freqs - 2 * cbar_margin
        cbar_x = n_times - cbar_width - max(1, int(n_times * 0.005))
        gradient = np.linspace(levels[0], levels[1], max(2, int(cbar_height))).reshape(-1, 1)
        gradient = np.repeat(gradient, cbar_width, axis=1)
        self._cbar_img.setImage(gradient.T)
        self._cbar_img.setLevels(levels)
        self._cbar_img.setRect(cbar_x, cbar_y, cbar_width, cbar_height)
        self._cbar_min_label.setText(f"{levels[0]:.1f}")
        self._cbar_max_label.setText(f"{levels[1]:.1f}")
        cbar_center_x = cbar_x + cbar_width / 2
        self._cbar_min_label.setPos(cbar_center_x, cbar_y)
        self._cbar_max_label.setPos(cbar_center_x, cbar_y + cbar_height)

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
