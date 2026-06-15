from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from scipy.signal import medfilt
import pyqtgraph as pg
import numpy as np
from utilities.timing_decorator import timing_decorator
from utilities.clock_time_format import parse_start_time, format_clock_time
from signal_processing import *


class HypnogramWidget(QWidget):
    changesMade = Signal()

    def __init__(self, centralWidget):
        super().__init__()

        # Plot axes
        self.axes = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("HypnogramWidget")
        self.axes.setBackground((0, 0, 0, 0))
        self.axes.setLabel("left", "Stage")
        self.axes.setMouseEnabled(x=False, y=False)

        # Colors
        self.colors = {
            -4: "#bf5656",
            -3: "#0b1c2c",
            -2: "#405c79",
            -1: "#aabcce",
            0: "#56bf8b",
            1: "#8bbf56",
            2: "#000000",
        }

        # Y axis
        self.axes.setYRange(-4, 2, padding=0)
        self.axes.getAxis("left").setTicks(
            [
                [
                    (-4.5, "N4"),
                    (-3.5, "N3"),
                    (-2.5, "N2"),
                    (-1.5, "N1"),
                    (-0.5, "REM"),
                    (0.5, "Wake"),
                    (1.5, "Event"),
                ]
            ]
        )
        self.kernel = 100
        self.comparison_items = []

    @timing_decorator
    def draw_hypnogram(self, ui):
        self.axes.clear()
        self.stage_items = {}
        self.event_items = []
        self.comparison_items = []
        self.times = np.arange(0, ui.numepo) * ui.config[0]["Epoch_length_s"] / 3600
        times = np.repeat(self.times, 2)
        stages = np.array([stage["digit"] for stage in ui.stages])
        for stage, color in self.colors.items():
            data = np.zeros(ui.numepo)
            data[:] = np.nan
            data[stages == stage] = stage
            data = np.concatenate(np.column_stack((data, data - 1)))
            pen = pg.mkPen(color=color, width=1)
            item = pg.PlotDataItem(times, data, pen=pen)
            self.axes.addItem(item)
            self.stage_items[stage] = item

        # Draw events
        self.draw_events(ui)

        # Axis limits
        self.axes.setXRange(times[0], times[-1], padding=0)

        # Initialize epoch indicator line
        self.epoch_indicator_line = pg.InfiniteLine(
            pos=self.times[0], angle=90, pen=pg.mkPen(color="k", width=1.5)
        )
        self.axes.addItem(self.epoch_indicator_line)

        # X axis ticks
        self._update_time_ticks(ui)

        # Draw comparison overlay (disagreement epochs in red)
        if getattr(ui, "stages_ref", None) is not None:
            self._draw_comparison_overlay(ui)

        # Draw SWA
        self.draw_swa_in_time(ui.swa)

    def draw_events(self, ui):
        times = np.repeat(self.times, 2)
        for container in ui.AnnotationContainer:
            epochs = np.unique(np.concatenate(container.epochs)).astype(int) - 1 if container.epochs else np.array([], dtype=int)
            if len(epochs) > 0:
                data = np.zeros(ui.numepo)
                data[:] = np.nan
                data[epochs] = 2
                data = np.concatenate(np.column_stack((data, data - 1)))
                pen = pg.mkPen(color=container.facecolor[0:3], width=2)
                item = pg.PlotDataItem(times, data, pen=pen)
                self.axes.addItem(item)
                self.event_items.append(item)

    def update_events(self, ui):
        for item in self.event_items:
            self.axes.removeItem(item)
        self.event_items = []
        self.draw_events(ui)

    def _update_time_ticks(self, ui):
        max_hour = int(self.times[-1])
        if max_hour < 1:
            self.axes.getAxis("bottom").setTicks([])
            return
        time_unit = ui.config[0].get("EEG_panel_time_unit", "Seconds")
        if time_unit == "Clock Time":
            start_s = parse_start_time(ui.config[0].get("Recording_start_time", "00:00"))
            hour_ticks = [(h, format_clock_time(start_s + h * 3600)) for h in range(1, max_hour + 1)]
        else:
            hour_ticks = [(h, f"{h}h") for h in range(1, max_hour + 1)]
        self.axes.getAxis("bottom").setTicks([hour_ticks])

    def update_time_axis(self, ui):
        self._update_time_ticks(ui)

    def _draw_comparison_overlay(self, ui):
        """Overlay disagreement epochs in red, showing the reference scoring's stage."""
        if not ui.disagreement_epochs:
            return

        times = np.repeat(self.times, 2)
        ref_digits = [s["digit"] for s in ui.stages_ref]

        # Collect (epoch, digit) pairs for disagreement epochs that have a digit
        ep_digit_pairs = [
            (ep, ref_digits[ep])
            for ep in ui.disagreement_epochs
            if ep < len(ref_digits) and ref_digits[ep] is not None
        ]
        if not ep_digit_pairs:
            return

        unique_vals = set(digit for _, digit in ep_digit_pairs)
        red_pen = pg.mkPen(color=(210, 40, 40), width=3)

        for stage_val in unique_vals:
            data = np.full(ui.numepo, np.nan)
            for ep, digit in ep_digit_pairs:
                if digit == stage_val:
                    data[ep] = stage_val
            data = np.concatenate(np.column_stack((data, data - 1)))
            item = pg.PlotDataItem(times, data, pen=red_pen)
            self.axes.addItem(item)
            self.comparison_items.append(item)





    def draw_swa_in_time(self, SWA):  
        self.swa_item = pg.PlotDataItem(
            self.times,
            SWA,
            pen=pg.mkPen(color=(0, 0, 0, 100)),
            width=2,
            style=Qt.DotLine,
        )
        self.scale_swa(SWA, self.kernel)
        self.axes.addItem(self.swa_item)

    def scale_swa(self, SWA, kernel):
        SWA = self.median_filter(SWA, kernel)
        # SWA = self.above_thresh_to_nan(SWA, kernel)
        self.kernel = kernel
        SWA = (SWA - np.nanmin(SWA)) / (np.nanmax(SWA) - np.nanmin(SWA))
        SWA = 5 * SWA - 4         
        self.swa_item.setData(self.times, SWA)

    def above_thresh_to_nan(self, SWA, kernel):
        threshold = np.nanpercentile(SWA, kernel)
        copySWA   = SWA.copy() 
        copySWA[copySWA > threshold] = np.nan
        return copySWA        

    def median_filter(self, SWA, kernel):
        kernel = self.make_even(kernel)
        SWA = medfilt(SWA, 101 - kernel)
        #SWA = -5 * SWA + 1
        return SWA
    
    def make_even(self, number):
        return number if number % 2 == 0 else number + 1


    @timing_decorator
    def update_hypnogram(self, ui):
        stages = np.array([stage["digit"] for stage in ui.stages])
        times = np.repeat(self.times, 2)
        for stage, item in self.stage_items.items():
            data = np.zeros(ui.numepo)
            data[:] = np.nan
            data[stages == stage] = stage
            data = np.concatenate(np.column_stack((data, data - 1)))
            item.setData(times, data)

    def update_epoch_indicator(self, this_epoch):
        self.epoch_indicator_line.setPos(self.times[this_epoch])

    def coordinates_upon_mousclick(self, event, epolen):
        if self.axes.sceneBoundingRect().contains(event.scenePos()):
            mouse_coordinates = self.axes.plotItem.vb.mapSceneToView(event.scenePos())
            this_epoch = np.round(mouse_coordinates.x() / epolen * 3600).astype(int)
            return this_epoch
