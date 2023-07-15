from PyQt5 import QtCore, QtWidgets, QtGui
import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from scipy.signal import welch, spectrogram, find_peaks
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
        self.axes.setLabel('left', 'Power', **{'color':'r', 'font-size':'20px'})
        self.axes.setMouseEnabled(x=False, y=False)
        self.axes.setXRange(0, 30, padding=0)    
        ticklabels = [(tick, f'{tick}Hz') for tick in np.round(np.arange(0, 30, 3), 1)]
        #ticklabels = [(tick, '') for tick in np.arange(0, 30, 2)]
        #for tick in np.arange(0, 30, 4):
        #    ticklabels[int(tick/2)] = (tick, f'{tick}Hz')
        self.axes.getAxis('bottom').setTicks([ticklabels])
        tick_font_size = QtGui.QFont()
        tick_font_size.setPointSize(10)  # Set the desired font size
        self.axes.getAxis('bottom').setStyle(tickFont= tick_font_size)          


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

        logp = np.log10(p)
        logp = (logp - min(logp)) / (max(logp) - min(logp))
        p = (p - min(p)) / (max(p) - min(p))

        # Plot power
        pen = pg.mkPen(width=4)
        #redpen = pg.mkPen(width=2, color=(233, 30, 99), style=QtCore.Qt.DashLine)
        self.axes.plot(f, p, pen=pen)
        #self.axes.plot(f, logp, pen=pg.mkPen(width=1, style=QtCore.Qt.DashLine))

        #self.axes.plot([maxf, maxf], [min(p), max(p)], pen=redpen)

        # Draw peaks
        self.axes.plotItem.showGrid(x=True, y=True, alpha=0.2 )
        #self.peak(f, p)

    def peak(self, f, p):
        xpeaks, ypeaks = find_peaks(p, height=max(p)*0.5, distance=2/np.unique(np.diff(f))[0])
        for xpeak in xpeaks:
            vertical_line = pg.InfiniteLine(pos=f[xpeak], angle=90, pen=pg.mkPen(color='r', width=0.8))
            self.axes.addItem(vertical_line)        



