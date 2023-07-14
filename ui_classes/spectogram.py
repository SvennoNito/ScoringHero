
from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
import numpy as np
from scipy.signal import welch, spectrogram


class spectogram(QtWidgets.QWidget):
    def __init__(self, centralWidget):
        self.freqs  = []
        self.times  = []
        self.epochs = []
        self.power  = []
        self.winlen = 4

        # Spectogram widget
        pg.setConfigOptions(imageAxisOrder='row-major')
        self.graphics = pg.GraphicsLayoutWidget(centralWidget)
        self.graphics.setObjectName("spectogram")
        self.graphics.setBackground('w')
        self.axes       = self.graphics.addPlot()
        #styles = {'color':'r', 'font-size':'20px'}
        #self.spectogram.setLabel('left', 'Frequency (Hz)', **styles)
        #self.spectogram.setLabel('bottom', 'Time (h)', **styles)  
        #self.graphics.scene().sigMouseClicked.connect(self.spectogramClick)

    def initiate(self, EEG):
        for epo in range(1, EEG.numepo):
            start = epo*EEG.epolen*EEG.srate - EEG.epolen*EEG.srate
            end   = epo*EEG.epolen*EEG.srate
            data  = EEG.data[0][int(start):int(end)]        

            [f, p] = welch(data, fs=EEG.srate, window='hann', nperseg=self.winlen*EEG.srate, detrend='constant', return_onesided=True, scaling='density', average='mean') 
            self.epochs.append(epo)
            self.power.append(list(p))    
            self.times.append(epo*EEG.epolen - EEG.epolen/2)
        self.freqs = np.array(f)
        self.power = np.array(self.power)
        self.times = np.array(self.times)
        self.image()

    def map(self, event):
        mouse_pos       = self.graphics.mapFromScene(event.scenePos())
        image_pos       = self.axes.mapFromParent(mouse_pos)
        image_coords    = self.axes.mapToView(image_pos)
        if image_coords.x() >= 0 and image_coords.x() < len(self.times):
           return round(image_coords.x())

    def image(self):
        # https://github.com/epeters13/pyqtspecgram/blob/main/src/pyqtspecgram/pyqtspecgram.py
        pg.setConfigOptions(imageAxisOrder='col-major')
        img = pg.ImageItem()
        img.setImage(self.power)
        img.setColorMap(pg.colormap.get('CET-L17'))
        img.setLevels([np.percentile(self.power, 5), np.percentile(self.power, 85)]) # Color scale   
        self.axes.addItem(img)
        self.axes.setLimits(xMin=0, xMax=len(self.times), yMin=0, yMax=len(self.freqs))
        #self.axes.setLabel('bottom', "Time", units='min')
        self.axes.setLabel('left', "Freq", units='Hz')

        self.axes.setXRange(0, len(self.times), padding=0)
        self.axes.setYRange(0, len(self.freqs), padding=0)

        # y ticks
        freqres = np.unique(np.diff(self.freqs))[0]
        yvals   = np.arange(0, 100, 5)
        yndx    = np.where(np.isin(self.freqs, yvals))[0] 
        ystr    = list(map(str, [int(y) for y in yndx * freqres]))
        yticks  = [(val, text) for val, text in zip(yndx, ystr)]
        self.axes.getAxis('left').setTicks([yticks, []])

        # xticks
        timeres = np.unique(np.diff(self.times))[0]
        xvals   = np.round(np.arange(0, 9900, 0.5), 1)
        xndx    = np.unique([(np.abs(self.times/60/60 - xval)).argmin() for xval in xvals])
        xstr    = list(map(str, [float(x) for x in xvals[0:len(xndx)]]))
        xticks  = [(val, f'{text} h') for val, text in zip(xndx, xstr)]
        self.axes.getAxis('bottom').setTicks([xticks, []])
        #self.axes.getAxis('bottom').setTicks([[], []])

        # Adjust layout
        layout = self.axes.getViewBox().parentWidget().layout
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)    
        self.axes.layout.setContentsMargins(0, 0, 0, 0)
        self.axes.vb.setContentsMargins(0, 0, 0, 0)

        pixel_size = self.times[-1]/(self.times.size-1)
        #img.setRect(QRectF(self.times[0]-pixel_size/2, self.freqs[0]-pixel_size/2, self.power.shape[1], self.power.shape[0]))
        #plt.pcolormesh(self.times, self.freqs, self.power)



        # [f, t, p] = spectrogram(EEG.data[0], fs=EEG.srate, window='hann', nperseg=int(4*EEG.srate), noverlap=0, detrend=False, scaling='density', axis=-1, mode='psd')
        # self.spec_times = self.spec_times
        # plot_spectogram(self)           