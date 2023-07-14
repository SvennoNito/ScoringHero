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
    def __init__(self, centralWidget):
        super().__init__()
        self.data    = []
        self.nchans  = []
        self.points  = []
        self.srate   = []
        self.numepo  = []
        self.epolen  = []
        self.shift   = 25
        self.scales  = []
        self.artefacts = []
        self.timesby = 1
        self.displayChannels = []
        self.channelColors   = []        

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

    def update(self, epolen):
        self.nchans  = len(self.data)
        self.points  = len(self.data[0])
        self.epolen  = epolen
        self.numepo  = int(np.floor(self.points / self.srate / epolen))
        self.scales  = np.ones(self.nchans)
        self.displayChannels = np.ones(self.nchans, dtype='bool')
        self.channelColors   = ['Black'] * (self.nchans-3) + ['Blue'] * 2 + ['Magenta']

    def showEEG(self, thisepoch):
        start      = thisepoch*self.epolen - self.epolen
        stop       = thisepoch*self.epolen
        ndxvecv    = np.arange(start*self.srate+1, stop*self.srate, 1, dtype=int) # Sample points to plot         
        timevec    = np.linspace(start/self.timesby, stop/self.timesby, num=len(ndxvecv)) # Build time vector       
 
        # Build dotted line
        dotted_pen  = pg.mkPen(color=(0, 0, 0), style=QtCore.Qt.DotLine)  
        dashed_pen  = pg.mkPen(color=(0, 0, 0, 25), style=QtCore.Qt.DashLine) 
        dotted_line = np.zeros(len(timevec))
        grid_pen    = pg.mkPen(color=(0, 0, 0, 15), style=QtCore.Qt.DashLine) 
        div_pen     = pg.mkPen(color=(100, 149, 237), style=QtCore.Qt.DotLine) 
   
        # Channel counter
        channelCount = 0

        # Loop through channels
        self.axes.clear()
        for count, channel in enumerate(self.data):
            pen = pg.mkPen(color=self.channelColorPalette[self.channelColors[count]])
            if self.displayChannels[count]:

                # Plot EEG
                self.axes.plot(timevec, channel[ndxvecv]*self.scales[count] - self.shift*self.nchans*channelCount, pen=pen, tag='EEG')

                # Set pen style to DotLine
                self.axes.plot(timevec, dotted_line - self.shift*self.nchans*channelCount + 37.5*self.scales[count], pen=dotted_pen)
                self.axes.plot(timevec, dotted_line - self.shift*self.nchans*channelCount - 37.5*self.scales[count], pen=dotted_pen)
                self.axes.plot(timevec, dotted_line - self.shift*self.nchans*channelCount - 0, pen=dashed_pen)
                
                # Add text
                if channelCount == 0 and thisepoch == 1:  # Only add text on the first channel
                    text1 = pg.TextItem(text="+37.5 \u03BCV", color='k', anchor=(0, 0.5))
                    text2 = pg.TextItem(text="-37.5 \u03BCV", color='k', anchor=(0, 0.5))
                    text1.setPos(timevec[0], 0-self.shift*self.nchans*channelCount + 37.5*self.scales[count])
                    text2.setPos(timevec[0], 0-self.shift*self.nchans*channelCount - 37.5*self.scales[count])  
                    font = QtGui.QFont(); font.setPixelSize(20)
                    text1.setFont(font)
                    text2.setFont(font)
                    self.axes.addItem(text1)
                    self.axes.addItem(text2)

                channelCount += 1

        
        # Adjust axis
        self.axes.setXRange(start/self.timesby, stop/self.timesby, padding=0)    
        self.axes.setYRange(-channelCount*self.shift*(self.nchans-0.5), self.shift*(self.nchans-0.5)/1.2, padding=0)  
        if self.timesby == 1:
            ticklabels = [(tick, f'{tick} s') for tick in np.round(np.arange(5, 10000, 5), 1)]
        elif self.timesby == 60:
            ticklabels = [(tick, f'{tick} min') for tick in np.round(np.arange(0.1, 2000, 0.1), 1)]

        self.axes.getAxis('bottom').setTicks([ticklabels]) 
        

        # 1s grid
        y_range = self.axes.getAxis('left').range
        for s in range(self.epolen):
            s = (s + self.epolen*(thisepoch-1)) /self.timesby
            self.axes.plot([s, s], [y_range[0], y_range[1]], pen=grid_pen)

        # grid parts
        for d in range(1, 6+1):
            partlen = self.epolen/6/self.timesby
            s = self.epolen*(thisepoch-1)/self.timesby + partlen*d
            self.axes.plot([s, s], [y_range[0], y_range[1]], pen=div_pen)
        

        # Show artefacts
        self.showArtefacts()

    def update_text(self, this_epoch, this_stage):
        self.textfield.setText(f'Epoch {this_epoch}/{self.numepo}: {this_stage}') 

    def scaleChannels(self, scaleDialogeBox, thisepoch):
        self.scales             = [spinbox.value() for spinbox in scaleDialogeBox.scaling_spinboxes]
        self.displayChannels    = [checkbox.isChecked() for checkbox in scaleDialogeBox.displayChannels]
        self.channelColors      = scaleDialogeBox.channelColors
        self.showEEG(thisepoch)       

    def storeArtefacts(self, greenLines):
        for line in greenLines.storedLines:
            self.artefacts.append(
                [round(greenLines.axes.plotItem.vb.mapSceneToView(line[0]).x(),3),
                round(greenLines.axes.plotItem.vb.mapSceneToView(line[1]).x(),3)]
            )
        unique_set      = []
        [unique_set.append(x) for x in self.artefacts if x not in unique_set]
        self.artefacts  = unique_set
        self.showArtefacts()

    def addArtefact(self, start, stop):
        self.artefacts.append([start, stop])
    
    def showArtefacts(self):
        y_range = self.axes.getAxis('left').range
        for artefact in self.artefacts:
            red_area = pg.LinearRegionItem(brush=(255, 0, 0, 100))
            red_area.setRegion([artefact[0], artefact[1], y_range[0], y_range[1]])
            self.axes.addItem(red_area)         

        # Remove dublicates
        region = []
        for item in self.axes.items():
            if isinstance(item, pg.LinearRegionItem):
                if item.getRegion() in region:
                    self.axes.removeItem(item)
                else:
                    region.append(item.getRegion())

    def removeArtefacts(self):
        xrange = self.axes.getAxis('bottom').range
        for artefact in self.artefacts.copy():
            if artefact[1] <= xrange[1] and artefact[0] >= xrange[0]:
                self.artefacts.remove(artefact)

        for item in self.axes.items():
            if isinstance(item, pg.LinearRegionItem):
                self.axes.removeItem(item)                        