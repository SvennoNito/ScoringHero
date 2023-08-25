from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
import pyqtgraph as pg
import numpy as np
from utilities import *
from signal_processing import *

class HypnogramWidget(QWidget):
    changesMade = Signal()

    def __init__(self, centralWidget):
        super().__init__()

        # Plot axes
        self.axes = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("HypnogramWidget")
        self.axes.setBackground((0, 0, 0, 0))
        self.axes.setLabel('left', 'Stage')
        self.axes.setMouseEnabled(x=False, y=False)

        # Colors
        self.colors = { -4: '#bf5656',
                        -3: '#0b1c2c',
                        -2: '#405c79',
                        -1: '#aabcce',
                         0: '#56bf8b',
                         1: '#8bbf56'}    

        # Y axis
        self.axes.setYRange(-4, 1, padding=0)     
        self.axes.getAxis('left').setTicks([[(-4.5, "N4"), (-3.5, "N3"), (-2.5, "N2"), (-1.5, "N1"), (-0.5, "R"), (0.5, "W")]])


    @timing_decorator
    def draw_hypnogram(self, scoring, numepo, config):

        self.axes.clear()
        # self.stage_items = []
        self.times  = np.arange(0, numepo) * config[0]['Epoch_length_s'] / 3600
        times       = np.repeat(self.times, 2) 
        stages      = np.array([stage['digit'] for stage in scoring])
        for stage, color in self.colors.items():
            data    = np.zeros(numepo)
            data[:] = np.nan
            data[stages == stage] = stage
            data    = np.concatenate(np.column_stack((data, data-1)))
            pen     = pg.mkPen(color=color, width=1)
            self.axes.plot(times, data, pen=pen)
            # item = pg.PlotDataItem(times, data, pen=pen)
            # self.stage_items.append(item)
            # self.axes.addItem(item)

        # Axis limits
        self.axes.setXRange(times[0], times[-1], padding=0)

        # Initialize epoch indicator line
        self.epoch_indicator_line = pg.InfiniteLine(pos=self.times[0], angle=90, pen=pg.mkPen(color='k', width=0.8))
        self.axes.addItem(self.epoch_indicator_line)   


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
             mouse_coordinates  = self.axes.plotItem.vb.mapSceneToView(event.scenePos())
             this_epoch         = np.round(mouse_coordinates.x()/epolen*3600).astype(int)
             return this_epoch        
                               