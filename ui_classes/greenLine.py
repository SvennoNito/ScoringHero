from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *

class greenLine(QtWidgets.QWidget):
    def __init__(self, dependingAxes, timefactor, areapower):
        super().__init__()
        self.pointLeftCorner  = QtCore.QPoint()
        self.pointRightCorner = QtCore.QPoint()
        self.width            = []
        self.height           = [] 
        self.storedLines      = []
        self.axes             = dependingAxes
        self.areapower        = areapower
        self.periodLength     = []
        self.totalLength      = 0
        self.artefactPeriods  = []
        self.timesby          = timefactor
        self.coordLeftCorner  = []
        self.coordRightCorner = []
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
        self.fliplr()
        self.respectBoundaries()
        self.adjustLength()
        self.update()
        self.transformCoordinates()
        self.showpower()

    def showpower(self):
        self.areapower.update(self.axes, self.coordLeftCorner, self.coordRightCorner)

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
        self.coordLeftCorner    = self.axes.plotItem.vb.mapSceneToView(self.pointLeftCorner)
        self.coordRightCorner   = self.axes.plotItem.vb.mapSceneToView(self.pointRightCorner)


    def reset(self):
        self.pointLeftCorner  = QtCore.QPoint()
        self.pointRightCorner = QtCore.QPoint()
        self.width            = []
        self.height           = [] 
        self.storedLines      = []
        self.periodLength     = []
        self.totalLength      = 0
        self.totalLengthLabel.setText(f"Total Length: {self.totalLength} s")
        self.update()   

    def labelArtefact(self):
        for line in self.storedLines:
            self.artefactPeriods.append(
                [self.axes.plotItem.vb.mapSceneToView(line[0]).x(),
                self.axes.plotItem.vb.mapSceneToView(line[1]).x()]
            )