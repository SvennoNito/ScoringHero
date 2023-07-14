from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from scipy.signal import welch, spectrogram
import numpy as np
import pyqtgraph as pg
  
class epochSpectrum:
    def __init__(self, EEG):
        self.freqs      = []
        self.times      = []
        self.power      = []
        self.freqres    = []
        self.sigmaRatio = []
        self.alphaRatio = []
        self.betaRatio  = []
        self.alpha      = []
        self.sigma      = []
        self.beta       = []
        self.computeSpectogram(EEG)
        self.computeFreqsOI()

    def computeSpectogram(self, EEG):
        for epo in range(1, EEG.numepo):
            start = epo*EEG.epolen*EEG.srate - EEG.epolen*EEG.srate + 1
            end   = epo*EEG.epolen*EEG.srate
            data  = EEG.data[0][int(start):int(end)]

            [f, t, pow] = spectrogram(
                data, fs=EEG.srate, window='hann', nperseg=int(EEG.srate*2), 
                noverlap=0, detrend=False, scaling='density', axis=-1, mode='psd')
            
            self.power.append(pow)

        self.times = t
        self.freqs = f
        self.freqres = np.unique(np.diff(self.freqs))[0]

    def computeFreqsOI(self):
        freqs_theta = np.where((self.freqs >= 5) & (self.freqs <= 7))[0]
        freqs_alpha = np.where((self.freqs >= 8) & (self.freqs <= 11))[0]
        freqs_sigma = np.where((self.freqs >= 12) & (self.freqs <= 16))[0]
        freqs_beta  = np.where((self.freqs >= 20) & (self.freqs <= 40))[0]          

        for epo in range(len(self.power)):
            self.sigmaRatio.append(np.mean(self.power[epo][freqs_sigma], axis=0) / np.mean(self.power[epo], axis=0))
            self.alphaRatio.append(np.mean(self.power[epo][freqs_alpha], axis=0) / np.mean(self.power[epo], axis=0))
            self.betaRatio.append(np.mean(self.power[epo][freqs_beta], axis=0) / np.mean(self.power[epo], axis=0))
            self.alpha.append(np.mean(self.power[epo][freqs_alpha], axis=0))
            self.sigma.append(np.mean(self.power[epo][freqs_sigma], axis=0))
            self.beta.append(np.mean(self.power[epo][freqs_beta], axis=0))

        ## Z standardize
        #self.sigmaRatio    = (self.sigmaRatio - np.median(self.sigmaRatio)) / stats.iqr(self.sigmaRatio)
        #self.alphaRatio    = (self.alphaRatio - np.median(self.alphaRatio)) / stats.iqr(self.alphaRatio)
        #self.alpha         = (self.alpha - np.median(self.alpha)) / stats.iqr(self.alpha)
        #self.sigma         = (self.sigma - np.median(self.sigma)) / stats.iqr(self.sigma)
        #self.beta          = (self.beta - np.median(self.beta)) / stats.iqr(self.beta)

    def drawLines(self, window, thisepo):
        window.clear()

        pen1    = pg.mkPen(color=(100, 149, 237), style=QtCore.Qt.SolidLine, width=3) 
        plot1   = window.plot(self.times, self.sigma[thisepo], pen=pen1)
        pen2    = pg.mkPen(color=(233, 30, 99), style=QtCore.Qt.SolidLine, width=3) 
        plot2   = window.plot(self.times, self.alpha[thisepo], pen=pen2)
        pen3    = pg.mkPen(color=(0, 0, 0), style=QtCore.Qt.DashLine, width=1.5) 
        plot3   = window.plot(self.times, self.beta[thisepo], pen=pen3)

        # Create legend item
        legend = window.addLegend()
        legend.addItem(plot1, 'Sigma')
        legend.addItem(plot2, 'Alpha')
        legend.addItem(plot3, 'Beta')
        # legend.setAutoFillBackground(True)
        window.setYRange(-1, 100)
        window.setXRange(0, 30)

        # X ticks
        ticklabels = [(tick, f'{tick} s') for tick in np.round(np.arange(0, 1000, 5), 0)]
        window.getAxis('bottom').setTicks([ticklabels])         
        #window.getAxis('left').setTicks([]) 

    def drawImage(self, window, thisepo):
        img = pg.ImageItem()
        img.setImage(self.power[thisepo])
        img.setColorMap(pg.colormap.get('CET-L17'))
        img.setLevels([np.percentile(self.power[thisepo], 15), np.percentile(self.power[thisepo], 90)]) # Color scale   
        window.addItem(img)    

        window.setLimits(xMin=0, xMax=self.power[thisepo].shape[1], yMin=0, yMax=self.power[thisepo].shape[0])
        # window.setLabel('bottom', "Time", units='s')
        #window.setLabel('left', "Frequency", units='Hz')

        # X and Y range
        window.setXRange(0, self.power[thisepo].shape[1])
        window.setYRange(0, self.power[thisepo].shape[0])
        window.setYRange(np.abs(self.freqs - 0).argmin(), np.abs(self.freqs - 40).argmin())

        # Y ticks
        yvals   = np.arange(0, 100, 5)
        yndx    = np.unique([(np.abs(self.freqs - yval)).argmin() for yval in yvals])
        #yndx    = np.where(np.isin(self.freqs, yvals))[0] 
        ystr    = list(map(str, [int(y) for y in yndx * self.freqres]))
        yticks  = [(val, text) for val, text in zip(yndx, ystr)]
        window.getAxis('left').setTicks([yticks, []])

        # xticks
        timeres = np.unique(np.diff(self.times[thisepo]))[0]
        xvals   = np.arange(0, 10000, 5) 
        xndx    = np.unique([(np.abs(self.times[thisepo] - xval)).argmin() for xval in xvals])
        xstr    = list(map(str, [int(x) for x in xvals[0:len(xndx)]]))
        xticks  = [(val, text) for val, text in zip(xndx, xstr)]
        window.getAxis('bottom').setTicks([xticks, []])   
        window.getAxis('bottom').setTicks([[], []])        
                
        # Adjust layout
        layout = window.getViewBox().parentWidget().layout
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)