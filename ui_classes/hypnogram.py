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
        self.A      = 'A'
        self.N1     = 'N1'
        self.N2     = 'N2'
        self.N3     = 'N3'
        self.N4     = 'N4'
        self.W      = 'Wake'
        self.REM    = 'REM'
        self.colors = { 2: '#FF0000',
                        1: '#8bbf56', 
                        0: '#56bf8b', 
                       -1: '#aabcce',
                       -2: '#405c79', 
                       -3: '#0b1c2c', 
                       -4: '#bf5656'}
        self.stages = []
        self.times  = []
        self.numepo = []
        self.epolen = []
        self.duration_h = []
        self.axes   = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("hypnogram")
        self.axes.setBackground('w')
        self.axes.setLabel('left', 'Stage', **{'color':'r', 'font-size':'20px'})
        self.axes.setMouseEnabled(x=False, y=False)
        #self.axes.setLabel('bottom', 'Time (h)', **{'color':'r', 'font-size':'16px'})

    def onclick(self, event):
        vb              = self.axes.plotItem.vb
        scene_coords    = event.scenePos()
        if self.axes.sceneBoundingRect().contains(scene_coords):
             mouse_point = vb.mapSceneToView(scene_coords)
             this_epoch  = np.round(mouse_point.x()/self.epolen*3600)
             return int(this_epoch)

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
        
    def express_uncertainty(self, this_epoch):
        if self.stages[this_epoch-1]['Uncertainty'] == 0:
            self.stages[this_epoch-1]['Uncertainty'] = 1
        else:
            self.stages[this_epoch-1]['Uncertainty'] = 0

    def get_next_uncertain(self):
        for index, stage in enumerate(self.stages):
            if stage['Uncertainty'] == 1:
                return index + 1            
        
    def get_text(self, this_epoch):
        return self.stages[this_epoch-1]['Stage'], self.stages[this_epoch-1]['Uncertainty']

    def assign(self, epoch, stage, channels):
        self.stages[epoch-1]['Stage'] = stage
        self.stages[epoch-1]['Digit'] = self.assign_number(stage)
        self.stages[epoch-1]['Channels'] = channels

    def get_next_unscored(self):
        for index, stage in enumerate(self.stages):
            if stage['Stage'] == '-':
                return index + 1       

    def get_next_transition(self, this_epoch):
        current_stage = self.stages[this_epoch-1]['Stage']
        for index in range(this_epoch, self.numepo):
            if self.stages[index]['Stage'] != current_stage:
                return index
        return this_epoch            

    def initiate(self, EEG):
        self.numepo     = EEG.numepo
        self.epolen     = EEG.epolen
        self.duration_h = EEG.duration_h      
        self.stages     = []          
        for epoch in range(1, self.numepo + 1):
            self.stages.append({'Epoch': epoch,
                                'Stage': '-',
                                'Digit': None,
                                'Channels': None,
                                'Uncertainty': 0}) 
        # self.stages = {int(key): ['-', None] for key in np.arange(1, self.numepo+1)}
        self.axes.setYRange(-4, 1, padding=0) 
        self.axes.setXRange(0, self.numepo, padding=0)
        yticks = [1.5, .5, -.5, -1.5, -2.5, -3.5]
        labels = [self.A, self.W, self.REM, self.N1, self.N2, self.N3]
        self.axes.getAxis('left').setTicks([[(yticks[count], label) for count, label in enumerate(labels)]])                                    
            
        # Time vector
        xt = np.arange(1, self.numepo+1)
        xt = xt*self.epolen/3600
        xt = np.repeat(xt, 2)    
        self.times = xt

        # Adjust axis
        self.axes.setXRange(0, max(self.times), padding=0)    
        self.axes.setYRange(min(yticks)-.5, max(yticks)+.5, padding=0)   
        ticklabels = [(tick, f'{tick}') for tick in np.arange(0, max(np.round(self.duration_h), 1), dtype=int)]
        for ndx in [-1]:
            ticklabels[ndx] = (ticklabels[ndx][0], f'{ticklabels[ndx][1]} h')        
        self.axes.getAxis('bottom').setTicks([ticklabels])         


    def moveTo(self, event):
        vb              = self.axes.plotItem.vb
        scene_coords    = event.scenePos()
        if self.axes.sceneBoundingRect().contains(scene_coords):
            mouse_point = vb.mapSceneToView(scene_coords)
            return np.round(mouse_point.x()/self.epolen*3600)

    def update(self, thisepo):
        self.axes.clear()

        stages = np.array([stage['Digit'] for stage in self.stages])
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

    def show_artefacts(self, epochs_with_artefacts):
        data            = np.zeros(self.numepo)
        data[:]         = np.nan
        data[epochs_with_artefacts] = 2        
        data            = np.concatenate(np.column_stack((data, data-1)))
        pen             = pg.mkPen(color=self.colors[2], width=4)
        self.axes.plot(self.times, data, pen=pen)        



    def add_to_spectogram(self, thisepo, axes, containers):

        stages = np.array([stage['Digit'] for stage in self.stages])
        limits = axes.getAxis('left').range
        times  = np.linspace(axes.getAxis('bottom').range[0], axes.getAxis('bottom').range[1], self.numepo) + 0.5
        times  = np.repeat(times, 2) 
        divideby = 6
        shift  = limits[1]/divideby

        for item in reversed(axes.items[2:-1]):
            axes.removeItem(item)

        for count, stage in enumerate([-3, -2, -1, 0, 1]):
            data    = np.zeros(self.numepo)
            data[:] = np.nan
            data[stages == stage] = stage
            data    = np.concatenate(np.column_stack((data+shift*count+limits[1]*0, data+shift*(count+1)+limits[1]*0)))
            pen     = pg.mkPen(color=(250, 250, 250, 180), width=4)
            axes.plot(times, data, pen=pen)

        # Artefacts
        for container in containers:
            data    = np.zeros(self.numepo)
            data[:] = np.nan
            data[container.epoch] = 2
            data    = np.concatenate(np.column_stack((data+shift*(divideby-1)+limits[1]*0, data+shift*divideby+limits[1]*0)))
            color   = container.facecolor[:-1]
            pen     = pg.mkPen(color=color, width=4)
            axes.plot(times, data, pen=pen)

        times  = np.linspace(axes.getAxis('bottom').range[0], axes.getAxis('bottom').range[1], self.numepo) + 0.5
        for stages in self.stages:
            if stages['Uncertainty'] == 1:
                index = stages['Epoch'] - 1
                question_mark = pg.TextItem('?', anchor=(0.5, 0.5), color=QtGui.QColor('black'))
                question_mark.setFont(QtGui.QFont('Arial', 15))
                question_mark.setPos(times[index], (divideby-1)*shift + shift/2)
                axes.addItem(question_mark)



        ## red line
       # pen  = pg.mkPen(color='#FA8072', width=1)
        #xt   = np.repeat(thisepo*self.epolen/3600, 2)
        #data = [-4, 1]
        #self.axes.plot(xt, data, pen=pen)
   