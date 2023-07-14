## Widget in which Hypnogram is displayed
#self.hypnogram = PlotWidget(self.centralwidget)
#self.hypnogram.setObjectName("hypnogram")
#self.hypnogram.setBackground('w')
#styles = {'color':'r', 'font-size':'20px'}
#self.hypnogram.setLabel('left', 'Stage', **styles)
#self.hypnogram.setLabel('bottom', 'Time (h)', **styles)  
#self.hypnogram.scene().sigMouseClicked.connect(self.hypnoClick)

from PyQt5 import QtCore, QtWidgets, QtGui
import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg

class hypnogram(QtWidgets.QWidget):
    def __init__(self, centralWidget):
        self.colors = { 1: '#8bbf56', 
                        0: '#56bf8b', 
                       -1: '#aabcce',
                       -2: '#405c79', 
                       -3: '#0b1c2c', 
                       -4: '#bf5656'}
        self.stages = {}
        self.times  = []
        self.numepo = []
        self.epolen = []
        self.axes   = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("hypnogram")
        self.axes.setBackground('w')
        self.axes.setLabel('left', 'Stage', **{'color':'r', 'font-size':'20px'})
        self.axes.setMouseEnabled(x=False, y=False)
        #self.axes.setLabel('bottom', 'Time (h)', **{'color':'r', 'font-size':'16px'})

    def assign_number(self, text):
        if text.lower() == "wake":
            return 1
        elif text.lower() == "rem":
            return 0
        elif text.lower() == "n1":
            return -1
        elif text.lower() == "n2":
            return -2
        elif text.lower() == "n3":
            return -3
        elif text.lower() == "n4":
            return -4
        else:
            return None            

    def assign_stage(self, epoch, stage):
        self.stages[epoch] = [stage, self.assign_number(stage)]

    def initiate(self, numepo, epolen):
        self.numepo = numepo
        self.epolen = epolen
        self.stages = {key: ['-', float("nan")] for key in np.arange(1, self.numepo+1, dtype=int)}
        self.axes.setYRange(-4, 1, padding=0) 
        self.axes.setXRange(0, self.numepo, padding=0)
        yticks = [.5, -.5, -1.5, -2.5, -3.5]
        labels = ['W', 'REM', 'N1', 'N2', 'N3']
        self.axes.getAxis('left').setTicks([[(yticks[count], label) for count, label in enumerate(labels)]])                                    
            
        # Time vector
        xt = np.arange(1, self.numepo+1)
        xt = xt*self.epolen/3600
        xt = np.repeat(xt, 2)    
        self.times = xt

        # Adjust axis
        self.axes.setXRange(0, max(self.times), padding=0)    
        self.axes.setYRange(min(yticks)-.5, max(yticks)+.5, padding=0)   
        ticklabels = [(tick, f'{tick} h') for tick in np.arange(0, 100, 0.5)]
        self.axes.getAxis('bottom').setTicks([ticklabels])         


    def moveTo(self, event):
        vb              = self.axes.plotItem.vb
        scene_coords    = event.scenePos()
        if self.axes.sceneBoundingRect().contains(scene_coords):
            mouse_point = vb.mapSceneToView(scene_coords)
            return np.round(mouse_point.x()/self.epolen*3600)

    def update(self, thisepo):
        self.axes.clear()
        stages = [val[1] for key, val in self.stages.items()]
        stages = np.array(stages)

        for stage, color in self.colors.items():
            data    = np.zeros(self.numepo)
            data[:] = np.nan
            data[stages == stage] = stage
            data    = np.concatenate(np.column_stack((data, data-1)))
            pen     = pg.mkPen(color=color, width=4)
            self.axes.plot(self.times, data, pen=pen)

        # red line
        pen  = pg.mkPen(color='#FA8072', width=1)
        xt   = np.repeat(thisepo*self.epolen/3600, 2)
        data = [-4, 1]
        self.axes.plot(xt, data, pen=pen)

   