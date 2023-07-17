from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import *

class greenLine(QtWidgets.QWidget):
    def __init__(self, areapower):
        super().__init__()
        self.pointLeftCorner  = QtCore.QPoint()
        self.pointRightCorner = QtCore.QPoint()
        self.width            = []
        self.height           = [] 
        self.storedLines      = []
        self.axes             = []
        self.areapower        = areapower
        self.periodLength     = []
        self.totalLength      = 0
        self.artefactPeriods  = []
        self.timesby          = []
        self.srate            = []
        self.coordLeftCorner  = []
        self.coordRightCorner = []
        self.amplitude        = []
        self.boxLeft          = []
        self.boxRight         = []
        self.boxBottom        = []
        self.boxTop           = []
        self.colorPalette     = {'grey': (150, 150, 150)} 
        self.fontSize         = 15
        self.show()

        # Create a label to display the totalLength value
        self.totalLengthLabel = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.totalLengthLabel.setFont(font)
        self.totalLengthLabel.setObjectName("totalLengthLabel")
        self.totalLengthLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self.totalLengthLabel.setText(f"Total Length: {self.totalLength} s")

        # Use QVBoxLayout for relative positioning
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.totalLengthLabel)    

    def initiate(self, EEG):
        self.axes    = EEG.axes
        self.timesby = EEG.timesby
        self.srate   = EEG.srate

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        br = QtGui.QBrush(QtGui.QColor(10, 100, 10, 40))  
        qp.setBrush(br)   
        for line, width, height in zip(self.storedLines, self.width, self.height):
            qp.drawRect(QtCore.QRect(line[0].x(), line[0].y(), width, height)) 
              
    def mousePressEvent(self, event):
        self.pointLeftCorner    = event.pos()
        self.pointRightCorner   = event.pos()
        self.storedLines.append([self.pointLeftCorner, self.pointRightCorner])
        self.width.append(self.pointRightCorner.x() - self.pointLeftCorner.x())
        self.height.append(self.pointRightCorner.y() - self.pointLeftCorner.y())
        self.update()

    def mouseMoveEvent(self, event):
        self.pointRightCorner   = event.pos()
        self.adjustLength()
        self.update()

    def mouseReleaseEvent(self, event):
        self.pointRightCorner = event.pos()
        if self.pointRightCorner != self.pointLeftCorner:
            self.fliplr()
            self.respectBoundaries()
            self.adjustLength()
            self.update() # draws the box
            self.transformCoordinates()
            self.show_amplitude()
            self.show_period()    

    def extract_eeg(self):

        # Extract EEG traces
        signals = self.axes.getPlotItem().listDataItems()
        signals = [signal.getData()[1] for signal in signals]
        signals = [signal for signal in signals if len(set(signal)) > 3] 

        # Adjust time values of green box to allign with EEG data time value
        xstart, xstop = self.boxLeft, self.boxRight
        epolen        = np.diff(self.axes.getAxis('bottom').range)[0]
        while xstart > epolen:
            xstart, xstop = xstart-epolen, xstop-epolen

        # Find correct EEG trace
        olap = []
        for signal in signals:
            xvals = np.where((signal <= self.boxTop) & (signal >= self.boxBottom))[0] / self.srate
            olap.append(sum((xvals <= xstop) & (xvals >= xstart)))
        trace = olap.index(max(olap))

        # Extract EEG signal during the time of the green box
        data = signals[trace][round(xstart*self.srate):round(xstop*self.srate)]
        self.amplitude = int(round(max(data) - min(data), 0))       

        # Compute power of that data
        self.areapower.update(data)         

    def show_amplitude(self):
        self.extract_eeg() # extract amplitude

        # text = pg.TextItem(text=f'{round(self.amplitude[-1])} \u03BCV', color='k', anchor=(0, .9))
        text = pg.TextItem(text=f'{self.amplitude} \u03BCV', color=self.colorPalette['grey'], anchor=(0, .9))
        text.setPos(self.boxLeft, self.boxTop)
        font = QtGui.QFont(); font.setPixelSize(self.fontSize)
        text.setFont(font)
        self.axes.addItem(text)    

    def show_period(self):
        text = pg.TextItem(text=f'{round(self.periodLength[-1], 2)} s', color=self.colorPalette['grey'], anchor=(0, 1)) # (100, 149, 237)
        text.setPos(self.boxRight, self.boxBottom)
        font = QtGui.QFont(); font.setPixelSize(self.fontSize)
        text.setFont(font)
        self.axes.addItem(text)              

    def adjustLength(self):
        self.storedLines[-1][1] = self.pointRightCorner
        self.width[-1]  = self.pointRightCorner.x() - self.pointLeftCorner.x()
        self.height[-1] = self.pointRightCorner.y() - self.pointLeftCorner.y()

    def fliplr(self):
        if self.pointLeftCorner.x() > self.pointRightCorner.x():
            tmp = self.pointLeftCorner.x()
            self.pointLeftCorner.setX(self.pointRightCorner.x())
            self.pointRightCorner.setX(tmp)

    def respectBoundaries(self):
        while self.axes.plotItem.vb.mapSceneToView(self.pointLeftCorner).x() < self.axes.getAxis('bottom').range[0]:
            self.pointLeftCorner.setX(self.pointLeftCorner.x()+1)
        while self.axes.plotItem.vb.mapSceneToView(self.pointRightCorner).x() > self.axes.getAxis('bottom').range[1]:
            self.pointRightCorner.setX(self.pointRightCorner.x()-1)
   

    def transformCoordinates(self):
        self.periodLength.append(self.axes.plotItem.vb.mapSceneToView(self.pointRightCorner).x()*self.timesby - self.axes.plotItem.vb.mapSceneToView(self.pointLeftCorner).x()*self.timesby)
        self.totalLength = round(sum(self.periodLength), 2)
        self.totalLengthLabel.setText(f"Total Length: {self.totalLength} s")
        if round(self.periodLength[-1], 1) != 0:
            self.totalLengthLabel.adjustSize()  

        # Transform to seconds and microvolt
        self.boxLeft     = self.axes.plotItem.vb.mapSceneToView(self.pointLeftCorner).x()
        self.boxRight    = self.axes.plotItem.vb.mapSceneToView(self.pointRightCorner).x()
        self.boxBottom   = min(self.axes.plotItem.vb.mapSceneToView(self.pointLeftCorner).y(), self.axes.plotItem.vb.mapSceneToView(self.pointRightCorner).y())
        self.boxTop      = max(self.axes.plotItem.vb.mapSceneToView(self.pointLeftCorner).y(), self.axes.plotItem.vb.mapSceneToView(self.pointRightCorner).y())
        # self.amplitude.append(self.boxTop - self.boxBottom)

        self.coordLeftCorner  = self.axes.plotItem.vb.mapSceneToView(self.pointLeftCorner)
        self.coordRightCorner = self.axes.plotItem.vb.mapSceneToView(self.pointRightCorner)


    def reset(self):
        self.pointLeftCorner  = QtCore.QPoint()
        self.pointRightCorner = QtCore.QPoint()
        self.width            = []
        self.height           = [] 
        self.storedLines      = []
        self.periodLength     = []
        self.amplitude        = []
        self.boxLeft          = []
        self.boxRight         = []
        self.boxBottom        = []
        self.boxTop           = []        
        self.totalLength      = 0
        self.totalLengthLabel.setText(f"Total Length: {self.totalLength} s")
        self.update()   

    def labelArtefact(self):
        for line in self.storedLines:
            self.artefactPeriods.append(
                [self.axes.plotItem.vb.mapSceneToView(line[0]).x(),
                self.axes.plotItem.vb.mapSceneToView(line[1]).x()]
            )