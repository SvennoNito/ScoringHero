from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from scipy.signal import medfilt
from itertools import chain
import pyqtgraph as pg
import numpy as np
from utilities.timing_decorator import timing_decorator
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

    @timing_decorator
    def draw_hypnogram(self, ui):
        self.axes.clear()
        # self.stage_items = []
        self.times = np.arange(0, ui.numepo) * ui.config[0]["Epoch_length_s"] / 3600
        times = np.repeat(self.times, 2)
        stages = np.array([stage["digit"] for stage in ui.stages])
        for stage, color in self.colors.items():
            data = np.zeros(ui.numepo)
            data[:] = np.nan
            data[stages == stage] = stage
            data = np.concatenate(np.column_stack((data, data - 1)))
            pen = pg.mkPen(color=color, width=1)
            self.axes.plot(times, data, pen=pen)
            # item = pg.PlotDataItem(times, data, pen=pen)
            # self.stage_items.append(item)
            # self.axes.addItem(item)    

        # Draw events
        self.draw_events(ui)
            
        # Axis limits
        self.axes.setXRange(times[0], times[-1], padding=0)

        # Initialize epoch indicator line
        self.epoch_indicator_line = pg.InfiniteLine(
            pos=self.times[0], angle=90, pen=pg.mkPen(color="k", width=1.5)
        )
        self.axes.addItem(self.epoch_indicator_line)

        # Remove x ticks
        self.axes.getAxis("bottom").setTicks([])

        # Draw SWA
        # SWA[SWA > np.median(SWA) + 1 * np.std(SWA)] = np.nan
        self.draw_swa_in_time(ui.swa)
        # self.axes.plot(self.times, SWA * (1 - (-4)) + (-4), pen=pg.mkPen(color=(11, 28, 44, 20)), width=.1, style=Qt.DotLine)

    def draw_events(self, ui):
        # self.times = np.arange(0, ui.numepo) * ui.config[0]["Epoch_length_s"] / 3600
        times = np.repeat(self.times, 2)        
        
        # Draw events
        for container in ui.AnnotationContainer:
            epochs = np.array(list(set(chain.from_iterable(container.epochs)))) - 1
            if len(epochs) > 0:
                data = np.zeros(ui.numepo)
                data[:] = np.nan                
                data[epochs] = 2
                data = np.concatenate(np.column_stack((data, data - 1)))
                pen = pg.mkPen(color=container.facecolor[0:3], width=2)
                self.axes.plot(times, data, pen=pen)        





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
    def update_hypnogram(self, scoring, numepo, this_epoch):
        return
        # this_stage   = scoring[this_epoch]['digit']
        # stages       = np.array([stage['digit'] for stage in scoring])
        # data         = np.zeros(numepo)
        # data[:]      = np.nan
        # data[stages == this_stage] = this_stage
        # data         = np.concatenate(np.column_stack((data, data-1)))
        # self.stage_items[this_stage + 4].setData(x=np.repeat(self.times, 2), y=data)

    def update_epoch_indicator(self, this_epoch):
        self.epoch_indicator_line.setPos(self.times[this_epoch])

    def coordinates_upon_mousclick(self, event, epolen):
        if self.axes.sceneBoundingRect().contains(event.scenePos()):
            mouse_coordinates = self.axes.plotItem.vb.mapSceneToView(event.scenePos())
            this_epoch = np.round(mouse_coordinates.x() / epolen * 3600).astype(int)
            return this_epoch
