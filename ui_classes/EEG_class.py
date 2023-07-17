from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
import numpy as np

"""         # Widget in which EEG data is displayed
self.widgetEEG = PlotWidget(self.centralwidget)
self.widgetEEG.setObjectName("widgetEEG")
self.widgetEEG.setBackground('w')
styles = {'color':'r', 'font-size':'20px'}
#self.widgetEEG.setLabel('left', 'Amplitude (\u03BCV)', **styles)
self.widgetEEG.setLabel('bottom', 'Time (s)', **styles)
self.widgetEEG.getAxis('left').setTickSpacing(1, 0) """

class EEG_class(QtWidgets.QWidget):
    changesMade = QtCore.pyqtSignal()

    def __init__(self, centralWidget):
        super().__init__()
        self.data    = []
        self.nchans  = []
        self.points  = []
        self.srate   = []
        self.numepo  = []
        self.epolen  = []
        self.shift   = 25
        self.artefacts  = []
        self.timesby    = 1     
        self.chaninfo   = {}
        self.times      = []
        self.duration_h = []

        # Widget for plotting
        self.axes = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("widgetEEG")
        self.axes.setBackground('w')
        #self.axes.getAxis('left').setTickSpacing(1, 0)
        self.axes.getAxis('left').setTicks([]) 
        #self.axes.setLabel('bottom', 'Time (min)', **{'color':'r', 'font-size':'20px'}) 
        self.channelColorPalette    = { 'Black': (0,0,0), 
                                        'Blue': (100, 149, 237), 
                                        'Magenta': (233, 30, 99)}
        
        # Widget for showing current epoch
        self.textfield = QtWidgets.QLabel(self.axes)
        self.textfield.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.textfield.setFont(font)
        self.textfield.setObjectName("textfield")
        #self.textfield.setStyleSheet("QLabel { color: red; font-size: 20px; text-align: center; }")

        # Layout
        layout = QtWidgets.QVBoxLayout(self.axes)
        layout.addWidget(self.textfield)


    def add_info(self, info):
        self.srate = info['SamplingRate']

    def add_chaninfo(self, chaninfo):
        self.chaninfo = chaninfo

    def update(self, epolen):
        self.nchans  = len(self.data)
        self.points  = len(self.data[0])
        self.epolen  = epolen
        self.numepo  = int(np.floor(self.points / self.srate / epolen))
        self.duration_h = self.points/self.srate/60/60
        self.data, self.times = self.epoch_data(self.epolen)

    def epoch_data(self, epolen):
        data_epoched = [[] for _ in range(self.nchans)]
        times        = []
        for epoch in range(1, self.numepo+1):
            start      = epoch*epolen - epolen
            stop       = epoch*epolen
            for channel in range(0, self.nchans):
                data_epoched[channel].append(self.data[channel][start*self.srate:stop*self.srate])
            times.append( np.linspace(start, stop, epolen*self.srate) / self.timesby) 

        return data_epoched, times
            

    def showEEG(self, this_epoch):
 
        # Build dotted line
        dotted_pen  = pg.mkPen(color=(0, 0, 0), style=QtCore.Qt.DotLine)  
        dashed_pen  = pg.mkPen(color=(0, 0, 0, 25), style=QtCore.Qt.DashLine) 
        dotted_line = np.zeros(len(self.times[this_epoch]))
        grid_pen    = pg.mkPen(color=(0, 0, 0, 15), style=QtCore.Qt.DashLine) 
        div_pen     = pg.mkPen(color=(100, 149, 237), style=QtCore.Qt.DotLine) 
   
        # Channel counter
        channelCount = 0

        # Loop through channels
        self.axes.clear()
        for count, channel in enumerate(self.data):
            pen = pg.mkPen(color=self.channelColorPalette[self.chaninfo[count]['Color']])
            if self.chaninfo[count]['Display']:

                # Plot EEG
                self.axes.plot(self.times[this_epoch-1], channel[this_epoch]*self.chaninfo[count]['Scale'] - self.shift*self.nchans*channelCount, pen=pen, tag='EEG')

                # Set pen style to DotLine
                self.axes.plot(self.times[this_epoch-1], dotted_line - self.shift*self.nchans*channelCount + 37.5*self.chaninfo[count]['Scale'], pen=dotted_pen)
                self.axes.plot(self.times[this_epoch-1], dotted_line - self.shift*self.nchans*channelCount - 37.5*self.chaninfo[count]['Scale'], pen=dotted_pen)
                self.axes.plot(self.times[this_epoch-1], dotted_line - self.shift*self.nchans*channelCount - 0, pen=dashed_pen)
                
                # Add +37.5 muV text on the first channel
                if channelCount == 0 and this_epoch == 1:
                    text1 = pg.TextItem(text="+37.5 \u03BCV", color=(150,150,150), anchor=(0, 0.5))
                    text2 = pg.TextItem(text="-37.5 \u03BCV", color=(150,150,150), anchor=(0, 0.5))
                    text1.setPos(self.times[this_epoch-1][0], 0-self.shift*self.nchans*channelCount + 37.5*self.chaninfo[count]['Scale'])
                    text2.setPos(self.times[this_epoch-1][0], 0-self.shift*self.nchans*channelCount - 37.5*self.chaninfo[count]['Scale'])  
                    font = QtGui.QFont(); font.setPixelSize(18)
                    text1.setFont(font)
                    text2.setFont(font)
                    self.axes.addItem(text1)
                    self.axes.addItem(text2)

                # Add channel labels
                text = pg.TextItem(text=self.chaninfo[count]['Channel'], color=(150,150,150), anchor=(0, 0.5))
                text.setPos(self.times[this_epoch-1][0], 0-self.shift*self.nchans*channelCount)  
                font = QtGui.QFont(); font.setPixelSize(20)
                text.setFont(font)
                self.axes.addItem(text)

                # Next channel
                channelCount += 1

        
        # Adjust axis
        self.axes.setXRange(self.times[this_epoch-1][0]/self.timesby, self.times[this_epoch-1][-1]/self.timesby, padding=0)    
        self.axes.setYRange(-channelCount*self.shift*(self.nchans-0.5), self.shift*(self.nchans-0.5)/1.2, padding=0)  
        if self.timesby == 1:
            ticklabels = [(tick, f'{tick} s') for tick in np.round(np.arange(5, 10000, 5), 1)]
        elif self.timesby == 60:
            ticklabels = [(tick, f'{tick} min') for tick in np.round(np.arange(0.1, 2000, 0.1), 1)]

        self.axes.getAxis('bottom').setTicks([ticklabels]) 
        

        # 1s grid
        y_range = self.axes.getAxis('left').range
        for s in range(self.epolen):
            s = (s + self.epolen*(this_epoch-1)) /self.timesby
            self.axes.plot([s, s], [y_range[0], y_range[1]], pen=grid_pen)

        # grid parts
        for d in range(1, 6+1):
            partlen = self.epolen/6/self.timesby
            s = self.epolen*(this_epoch-1)/self.timesby + partlen*d
            self.axes.plot([s, s], [y_range[0], y_range[1]], pen=div_pen)
        

        # Show artefacts
        self.changesMade.emit()

    def update_text(self, this_epoch, this_stage):
        self.textfield.setText(f'Epoch {this_epoch}/{self.numepo}: {this_stage}') 

    def scaleChannels(self, chaninfo, this_epoch):
        self.chaninfo = chaninfo
        self.showEEG(this_epoch)       

