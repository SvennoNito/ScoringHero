
from PyQt5 import  QtWidgets, QtGui
import pyqtgraph as pg
import numpy as np
from scipy.signal import welch, find_peaks

class spectogram(QtWidgets.QWidget):
    def __init__(self, centralWidget):
        self.winlen         = 4
        self.img            = []
        self.vline          = None
        self.lower_limit_hz = 0
        self.upper_limit_hz = 20

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

    def change_configuration(self, configuration):
        self.lower_limit_hz = configuration['Spectogram_lower_limit_hz']
        self.upper_limit_hz = configuration['Spectogram_upper_limit_hz']*6/5   

    def initiate(self, EEG):
        super().__init__()
        self.freqs  = []
        self.times  = []
        self.power  = []
        self.epochs = []

        for epo in range(EEG.numepo):
            [f, p] = welch(EEG.data[EEG.chan_main][epo], fs=EEG.srate, window='hann', nperseg=self.winlen*EEG.srate, detrend='constant', return_onesided=True, scaling='density', average='mean') 
            self.epochs.append(epo)
            self.power.append(list(p))    
            self.times.append(epo*EEG.epolen - EEG.epolen/2)
        self.freqs = np.array(f)
        self.power = np.array(self.power)
        self.times = np.array(self.times)            

        # Frequencies of interest
        self.power = np.array([power[(self.freqs >= self.lower_limit_hz) & (self.freqs <= self.upper_limit_hz)] for power in self.power])
        self.freqs = self.freqs[(self.freqs >= self.lower_limit_hz) & (self.freqs <= self.upper_limit_hz)]
        self.white_top()
        self.build_image()

    def white_top(self):
        #steps = len(self.freqs) / 6 - self.freqs
        #start = steps.tolist().index(min(steps))
        start           = round(len(self.freqs) - len(self.freqs) / 6)
        replace_with    = np.percentile(self.power, 50+2.5/2)
        for power in self.power:
            power[start:] = np.nan
        self.power = np.array(self.power)

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
        self.img.setColorMap(pg.colormap.get('CET-D1A'))
        self.img.setLevels([np.nanpercentile(self.power, 0), np.nanpercentile(self.power, 95)]) # Color scale     
        self.image()    

    def image(self):
        self.axes.clear()
        self.axes.addItem(self.img)
        self.axes.setLimits(xMin=0, xMax=len(self.times), yMin=0, yMax=len(self.freqs))
        #self.axes.setLabel('bottom', "Time", units='min')
        self.axes.setLabel('left', "Freq", units='Hz', **{'color':'r', 'font-size':'18px'})

        self.axes.setXRange(0, len(self.times), padding=0)
        self.axes.setYRange(0, len(self.freqs), padding=0)

        # y ticks
        freqres = np.unique(np.diff(self.freqs))[0]
        yvals   = np.arange(0, self.upper_limit_hz*5/6, 5)
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


class powerbox(QtWidgets.QWidget):
    def __init__(self, centralWidget):
        self.power          = []
        self.srate          = []
        self.epolen         = []
        self.data           = []
        self.srate          = []
        self.epolen         = []
        self.winlen         = 2
        self.lower_limit_hz = 0
        self.upper_limit_hz = 26

        # Plot widget
        self.axes   = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("epochpower")
        self.axes.setBackground('w')
        self.axes.getAxis('left').setTicks([]) 
        self.axes.setLabel('left', 'Power', **{'color':'r', 'font-size':'20px'})
        self.axes.setMouseEnabled(x=False, y=False)
        self.axes.setXRange(0, 30, padding=0)    
        #self.axes.setLogMode(x=True)
        #ticklabels = [(tick, f'{tick}') for tick in np.round(np.arange(0, 30, 1), 1)]
        #for ndx in [-1]:
        #    ticklabels[ndx] = (ticklabels[ndx][0], f'{ticklabels[ndx][1]} Hz')
        #ticklabels = [(tick, '') for tick in np.arange(0, 30, 2)]
        #for tick in np.arange(0, 30, 4):
        #    ticklabels[int(tick/2)] = (tick, f'{tick}Hz')
        #self.axes.getAxis('bottom').setTicks([ticklabels])
        tick_font_size = QtGui.QFont()
        tick_font_size.setPointSize(8)  # Set the desired font size
        self.axes.getAxis('bottom').setStyle(tickFont= tick_font_size)      

    def change_configuration(self, configuration):
        self.lower_limit_hz = configuration['Area_power_lower_limit_hz']
        self.upper_limit_hz = configuration['Area_power_upper_limit_hz']              

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
        p = p[np.where((f <= self.upper_limit_hz) & (f >= self.lower_limit_hz))]
        f = f[np.where((f <= self.upper_limit_hz) & (f >= self.lower_limit_hz))]

        # Create stretched frequency vector
        #expvector = np.exp(np.linspace(0, 2, 31))
        #distances = np.diff(expvector)
        #midpoint  = max(distances) + np.diff(distances[-2:])*1.5
        #fmod      = np.cumsum(np.concatenate((distances, midpoint, distances[::-1])))
        fmod      = np.exp(np.linspace(0, 2, len(f)))
        fmod      = np.linspace(0, 2, len(f))

        # Ticklabels
        ticklabels  = []
        tickvals    = np.arange(min(f), max(f), 2)
        indices     = [np.where(val == f)[0][0] for val in tickvals]
        for index, tickval in zip(indices, tickvals):
            ticklabels.append((fmod[index], f'{int(tickval)}'))
        self.axes.getAxis('bottom').setTicks([ticklabels])        

        # Visible axes
        self.axes.setXRange(min(fmod), max(fmod), padding=0) 
        self.axes.plotItem.showGrid(x=True, y=True, alpha=0.3)

        # Scale power values
        logp = np.log10(p)
        logp = (logp - min(logp)) / (max(logp) - min(logp))
        p = (p - min(p)) / (max(p) - min(p))

        # Plot power
        pen = pg.mkPen(width=4)
        self.axes.plot(fmod, p, pen=pen)


        # Plot power
        #redpen = pg.mkPen(width=2, color=(233, 30, 99), style=QtCore.Qt.DashLine)  
        #self.axes.plot(f, logp, pen=pg.mkPen(width=1, style=QtCore.Qt.DashLine))
        #self.axes.plot([maxf, maxf], [min(p), max(p)], pen=redpen)

        # Draw peaks
        #self.peak(f, p)

    def peak(self, f, p):
        xpeaks, ypeaks = find_peaks(p, height=max(p)*0.5, distance=2/np.unique(np.diff(f))[0])
        for xpeak in xpeaks:
            vertical_line = pg.InfiniteLine(pos=f[xpeak], angle=90, pen=pg.mkPen(color='r', width=0.8))
            self.axes.addItem(vertical_line)        



