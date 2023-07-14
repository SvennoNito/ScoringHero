from PyQt5 import QtCore, QtWidgets, QtGui
import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from scipy.signal import welch, spectrogram
from scipy.stats import iqr

class areapower(QtWidgets.QWidget):
    def __init__(self, centralWidget):
        self.power          = []
        self.srate          = []
        self.epolen         = []
        self.data           = []
        self.srate          = []
        self.epolen         = []
        self.winlen         = 2

        # Plot widget
        self.axes   = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("epochpower")
        self.axes.setBackground('w')
        self.axes.getAxis('left').setTicks([]) 
        # self.axes.setLabel('left', 'Stage', **{'color':'r', 'font-size':'20px'})
        self.axes.setMouseEnabled(x=False, y=False)
        self.axes.setXRange(0, 30, padding=0)    
        ticklabels = [(tick, f'{tick} Hz') for tick in np.round(np.arange(0, 30, 5), 1)]
        self.axes.getAxis('bottom').setTicks([ticklabels])        

    def initiate(self, EEG):
        # self.data   = EEG.data
        self.srate  = EEG.srate
        self.epolen = EEG.epolen

    def update(self, data):   
        self.axes.clear()

        # Compute power
        nperseg = min(len(data), self.winlen*self.srate)
        [f, p]  = welch(data, fs=self.srate, window='hann', nperseg=nperseg, nfft=self.winlen*self.srate, detrend='constant', return_onesided=True, scaling='density', average='mean') 
        maxf    = f[np.where(p==max(p))[0][0]]

        # Frequencies of interest
        f = f[np.where(f <= 30)]
        p = p[np.where(f <= 30)]

        # Plot power
        pen = pg.mkPen(width=4)
        redpen = pg.mkPen(width=2, color=(233, 30, 99), style=QtCore.Qt.DashLine)
        self.axes.plot(f, p, pen=pen)
        self.axes.plot([maxf, maxf], [min(p), max(p)], pen=redpen)


