
from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
import numpy as np
from scipy.signal import welch, spectrogram


class spectogram(QtWidgets.QWidget):
    def __init__(self, centralWidget):
        self.winlen = 4
        self.img    = []
        self.vline  = None

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
        self.freqs  = []
        self.times  = []
        self.power  = []
        self.epochs = []

        for epo in range(EEG.numepo):
            [f, p] = welch(EEG.data[0][epo], fs=EEG.srate, window='hann', nperseg=self.winlen*EEG.srate, detrend='constant', return_onesided=True, scaling='density', average='mean') 
            self.epochs.append(epo)
            self.power.append(list(p))    
            self.times.append(epo*EEG.epolen - EEG.epolen/2)
        self.freqs = np.array(f)
        self.power = np.array(self.power)
        self.times = np.array(self.times)
        self.build_image()

    def map(self, event):
        mouse_pos       = self.graphics.mapFromScene(event.scenePos())
        image_pos       = self.axes.mapFromParent(mouse_pos)
        image_coords    = self.axes.mapToView(image_pos)
        if image_coords.x() >= 0 and image_coords.x() < len(self.times):
           return int(np.ceil(image_coords.x()))
        
    def add_line(self, this_epoch):
        if self.vline is not None:
            self.axes.removeItem(self.vline)
        self.vline = pg.InfiniteLine(pos=this_epoch-0.5, angle=90, pen=pg.mkPen(color='k', width=0.8))
        self.axes.addItem(self.vline)

    def build_image(self):
        # https://github.com/epeters13/pyqtspecgram/blob/main/src/pyqtspecgram/pyqtspecgram.py
        pg.setConfigOptions(imageAxisOrder='col-major')
        self.img = pg.ImageItem()
        self.img.setImage(self.power)
        self.img.setColorMap(pg.colormap.get('CET-D9'))
        self.img.setLevels([np.percentile(self.power, 0), np.percentile(self.power, 97.5)]) # Color scale     
        self.image()    


    def image(self):
        self.axes.clear()
        self.axes.addItem(self.img)
        self.axes.setLimits(xMin=0, xMax=len(self.times), yMin=0, yMax=len(self.freqs))
        #self.axes.setLabel('bottom', "Time", units='min')
        self.axes.setLabel('left', "Freq", units='Hz', **{'color':'r', 'font-size':'20px'})

        self.axes.setXRange(0, len(self.times), padding=0)
        self.axes.setYRange(0, len(self.freqs[self.freqs <= 30]), padding=0)

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

        ## Adjust layout
        #layout = self.axes.getViewBox().parentWidget().layout
        #layout.setSpacing(0)
        #layout.setContentsMargins(0, 0, 0, 0)    
        ##self.axes.layout.setContentsMargins(0, 0, 0, 0)
        #self.axes.vb.setContentsMargins(0, 0, 0, 0)

        pixel_size = self.times[-1]/(self.times.size-1)
        #img.setRect(QRectF(self.times[0]-pixel_size/2, self.freqs[0]-pixel_size/2, self.power.shape[1], self.power.shape[0]))
        #plt.pcolormesh(self.times, self.freqs, self.power)