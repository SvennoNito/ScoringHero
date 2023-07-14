from PyQt5 import QtCore, QtWidgets, QtGui
import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from scipy.signal import welch, spectrogram
from scipy.stats import iqr
from mne.time_frequency import morlet

class epochpower(QtWidgets.QWidget):
    def __init__(self, centralWidget):
        self.colors = { 1: '#8bbf56', 
                        0: '#56bf8b', 
                       -1: '#aabcce',
                       -2: '#405c79', 
                       -3: '#0b1c2c', 
                       -4: '#bf5656'}
        self.powerf13       = []
        self.powerf10       = []
        self.powerf30       = []
        self.timesby        = []
        self.srate          = []
        self.epolen         = []

        # Plot widget
        self.axes   = pg.PlotWidget(centralWidget)
        self.axes.setObjectName("epochpower")
        self.axes.setBackground('w')
        self.axes.getAxis('left').setTicks([]) 
        # self.axes.setLabel('left', 'Stage', **{'color':'r', 'font-size':'20px'})
        self.axes.setMouseEnabled(x=False, y=False)
        #self.axes.setLabel('bottom', 'Time (h)', **{'color':'r', 'font-size':'16px'})

    def update(self, thisepoch):   
        self.axes.clear()

        # Epoch
        start      = thisepoch*self.epolen - self.epolen
        stop       = thisepoch*self.epolen
        ndxvecv    = np.arange(start*self.srate+1, stop*self.srate, 1, dtype=int) # Sample points to plot         
        timevec    = np.linspace(start/self.timesby, stop/self.timesby, num=len(ndxvecv)) # Build time vector       

        # Plot
        solid_pen   = pg.mkPen(color=(0, 0, 0), style=QtCore.Qt.SolidLine, width=3)     
        red_pen     = pg.mkPen(color=(233, 30, 99), style=QtCore.Qt.DotLine, width=1.2)  
        blue_pen    = pg.mkPen(color=(100, 149, 237), style=QtCore.Qt.DashLine, width=3)               
        dotted_pen  = pg.mkPen(color=(0, 0, 0), style=QtCore.Qt.DotLine, width=2) 

        self.axes.addLegend(offset=(0, 0.1))
        self.axes.plot(timevec, self.powerf13[ndxvecv], pen=solid_pen, name='sigma')
        self.axes.plot(timevec, self.powerf10[ndxvecv], pen=blue_pen, name='alpha')
        self.axes.plot(timevec, self.powerf30[ndxvecv], pen=red_pen, name='beta')

        # self.axes.plot(timevec, np.ones(len(ndxvecv))*self.thresh, pen=dotted_pen)

        # Adjust axis
        self.axes.setXRange(start/self.timesby, stop/self.timesby, padding=0)    
        self.axes.setYRange(0, np.percentile(self.powerf13, 99), padding=0)  

        # Axis ticks
        if self.timesby == 1:
            ticklabels = [(tick, f'{tick} s') for tick in np.round(np.arange(5, 10000, 5), 1)]
        elif self.timesby == 60:
            ticklabels = [(tick, f'{tick} min') for tick in np.round(np.arange(0.1, 2000, 0.1), 1)]
        self.axes.getAxis('bottom').setTicks([ticklabels]) 


    def initiate(self, EEG):
        self.srate      = EEG.srate
        self.timesby    = EEG.timesby
        self.epolen     = EEG.epolen

        # https://raphaelvallat.com/spindles.html
        # Convolve the wavelet and extract magnitude and phase
        power = []
        for cf in range(11,16+1):
            #cf = 13     # Central spindles frequency in Hz
            nc = 14     # Number of oscillations in the spindles       
            wlt            = morlet(self.srate, [cf], n_cycles=nc)[0] # Compute the wavelet
            analytic       = np.convolve(EEG.data[1], wlt, mode='same') # Convolve the wavelet
            magnitude      = np.abs(analytic) # extract magnitude
            power.append(np.square(magnitude)) # Compute power
        self.powerf13  = np.mean(power, axis=0)
        self.powerf13  = self.powerf13 / iqr(self.powerf13) # Normalize power          
        # phase        = np.angle(analytic)

        # Convolve the wavelet and extract magnitude and phase
        power = []
        for cf in range(8,10+1):
            #cf = 13     # Central spindles frequency in Hz
            nc = 9     # Number of oscillations in the spindles       
            wlt            = morlet(self.srate, [cf], n_cycles=nc)[0] # Compute the wavelet
            analytic       = np.convolve(EEG.data[1], wlt, mode='same') # Convolve the wavelet
            magnitude      = np.abs(analytic) # extract magnitude
            power.append(np.square(magnitude)) # Compute power
        self.powerf10  = np.mean(power, axis=0)
        self.powerf10  = self.powerf10 / iqr(self.powerf10) # Normalize power      

        power = []
        for cf in range(20,30+1):
            #cf = 13     # Central spindles frequency in Hz
            nc = 25     # Number of oscillations in the spindles       
            wlt            = morlet(self.srate, [cf], n_cycles=nc)[0] # Compute the wavelet
            analytic       = np.convolve(EEG.data[1], wlt, mode='same') # Convolve the wavelet
            magnitude      = np.abs(analytic) # extract magnitude
            power.append(np.square(magnitude)) # Compute power
        self.powerf30  = np.mean(power, axis=0)
        self.powerf30  = self.powerf30 / iqr(self.powerf30) # Normalize power       

        # self.powerf13 = (power - power.min()) / (power.max() - power.min()) # sensitive to outliers
        # self.thresh     = np.percentile(self.powerf13, 50)
        # supra_thresh = np.where(self.powerf13 >= self.thresh)[0] # Find supra-threshold values     
        # val_spindles = np.nan * np.zeros(EEG.data[0].size) # Create vector for plotting purposes
        # val_spindles[supra_thresh] = EEG.data[0][supra_thresh]      

        """ # Plot
        t = np.arange(wlt.size) / sf
        fig, ax = plt.subplots(1, 1, figsize=(7, 4))
        ax.plot(t, wlt)
        plt.ylim(-0.4, 0.4)
        plt.xlim(t[0], t[-1])
        plt.xlabel('Time [seconds]')
        plt.ylabel('Amplitude [a.u.]')  """               

        """ # Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
        ax1.plot(times, x, lw=1.5)
        ax1.plot(times, val_spindles, color='indianred', alpha=.8)
        ax1.set_xlim(0, times[-1])
        ax1.set_ylabel('Voltage [uV]')
        ax1.set_title('Cz EEG signal')

        ax2.plot(norm_power)
        ax2.set_xlabel('Time [sec]')
        ax2.set_ylabel('Normalized wavelet power')
        ax2.axhline(thresh, ls='--', color='indianred', label='Threshold')
        ax2.fill_between(times, norm_power, thresh, where = norm_power >= thresh,
                        color='indianred', alpha=.8)
        plt.legend(loc='best') """