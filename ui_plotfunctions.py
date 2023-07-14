import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui
import matplotlib.pyplot as plt

def plotEpoch(main):

    # Sample points to plot
    start_sec = main.epochDisplay*main.epochLen_sec - main.epochLen_sec + 1
    end_sec   = main.epochDisplay*main.epochLen_sec
    ndxvec    = np.arange(start_sec*main.EEG.srate+1, end_sec*main.EEG.srate, 1, dtype=int)
    
    # Build time vector       
    timevec   = np.linspace(start_sec, end_sec, num=len(ndxvec))

    # Build dotted line
    dotted_pen  = pg.mkPen(color=(0, 0, 0), style=QtCore.Qt.DotLine)  
    dashed_pen  = pg.mkPen(color=(0, 0, 0, 25), style=QtCore.Qt.DashLine) 
    dotted_line = np.zeros(len(timevec))
    
    # Channel counter
    channelCount = 0

    # Color
    channelColors = {'Black': (0,0,0), 'Blue': (100, 149, 237), 'Magenta': (233, 30, 99)}

    # Loop through channels
    main.widgetEEG.clear()
    for count, channel in enumerate(main.EEG.data):
        pen = pg.mkPen(color=channelColors[main.channelColors[count]])
        if main.displayChannels[count]:

            # Plot EEG
            main.widgetEEG.plot(timevec, channel[ndxvec]*main.scales[count] - main.shift*main.EEG.nchans*channelCount, pen=pen)
            
            # Set pen style to DotLine
            main.widgetEEG.plot(timevec, dotted_line - main.shift*main.EEG.nchans*channelCount + 37.5*main.scales[count], pen=dotted_pen)
            main.widgetEEG.plot(timevec, dotted_line - main.shift*main.EEG.nchans*channelCount - 37.5*main.scales[count], pen=dotted_pen)
            main.widgetEEG.plot(timevec, dotted_line - main.shift*main.EEG.nchans*channelCount - 0, pen=dashed_pen)
            channelCount += 1
    
    # Adjust axis
    main.widgetEEG.setXRange(start_sec, end_sec, padding=0)    
    main.widgetEEG.setYRange(-channelCount*main.shift*(main.EEG.nchans-0.5), main.shift*(main.EEG.nchans-0.5)/1.2, padding=0)    


def plot_spectogram(main):
    1