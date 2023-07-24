from PyQt5 import QtWidgets, QtCore, QtGui, QtCore
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np

class container(QtCore.QObject):
    changesMade = QtCore.pyqtSignal()
    def __init__(self, epolen, facecolor=(255, 200, 200, 100), label='Artefact', parent=None):
        super().__init__(parent)
        self.borders    = []
        self.epoch      = []
        self.facecolor  = facecolor
        self.epolen     = epolen
        self.label      = label

    def include(self, greenLines):
        whole_epoch     = greenLines.axes.getAxis('bottom').range # epoch range
        #all_borders     = [annotation.borders[0] for annotation in allAnnotations] # all borders
        #all_borders     = [border[0] for border in all_borders if len(border) > 0]
        areas_in_epoch  = [item[0] > whole_epoch[0] and item[1] < whole_epoch[1] for item in self.borders] # artefacts in epoch

        # Remove whole epoch if already marked
        if whole_epoch in self.borders:
            self.borders.remove(whole_epoch) 
            self.remove_areas(greenLines)        

        else: # whole epoch was not marked
            if len(greenLines.storedLines) == 0: # No green lines, store whole epoch?
                if any(areas_in_epoch): # epoch already has artefacts, remove those artefacts
                    for index in np.where(areas_in_epoch)[0][::-1]:
                        self.borders.remove(self.borders[index])
                    self.remove_areas(greenLines)
                elif whole_epoch not in self.borders: # store whole epoch
                    self.borders.append(whole_epoch)
                    self.show_areas(greenLines)
            else: # there are greeb lines
                newArtefacts = []
                for line in greenLines.storedLines: # get all green lines
                    newArtefacts.append([
                        round(greenLines.axes.plotItem.vb.mapSceneToView(line[0]).x(),3),
                        round(greenLines.axes.plotItem.vb.mapSceneToView(line[1]).x(),3)])
                newArtefacts = [item for item in newArtefacts if item[0] != item[1]] # Remove dublicates

                if not all(item in self.borders for item in newArtefacts): # If there are new artefacts
                    for item in newArtefacts: # Store those new artefacts
                        if item not in self.borders:
                            self.borders.append(item)
                    self.show_areas(greenLines)
                    self.remove_green_areas(greenLines)
                else: # No new artefacts
                    for item in newArtefacts: # Remove all artefacts
                        self.borders.remove(item)
                    self.remove_areas(greenLines) # Remove all red areas

        # Order artefacts based on time
        self.borders.sort()
        self.related_epoch()

    def remove_green_areas(self, greenLines):
        greenLines.reset()
        greenLines.update()          

    def related_epoch(self):
        self.epoch = []
        for border in self.borders:
            self.epoch.append(int(np.ceil(border[1] / self.epolen)))

    def add_instance(self, borders):
        for border in borders:
            self.border.append([border[0], border[1]])  

    def remove_areas(self, AxesEEG):
        for item in AxesEEG.axes.items():
            if isinstance(item, pg.LinearRegionItem):
                rgb = item.brush.color()
                if self.facecolor == (rgb.red(), rgb.green(), rgb.blue(), rgb.alpha()):
                    AxesEEG.axes.removeItem(item)

    def show_areas(self, AxesEEG):
        previous_areas  = [item.getRegion() for item in AxesEEG.axes.items() if isinstance(item, pg.LinearRegionItem)]
        for border in self.borders:
            red_area = pg.LinearRegionItem(brush=self.facecolor, pen=pg.mkPen(color=(0, 0, 0), width=2))
            red_area.setRegion([border[0], border[1]]) 
            if tuple(border) not in previous_areas:     
                AxesEEG.axes.addItem(red_area)   

        #for item in greenLines.axes.items(): # Remove all areas
        #    if isinstance(item, pg.LinearRegionItem):
        #        greenLines.axes.removeItem(item)                          




class editbox(QtWidgets.QDialog):
    changesMade = QtCore.pyqtSignal()

    def __init__(self, annotation_containers, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.countbox = []
        self.labelbox = []
        self.colorbox = []    
        self.colorpick = [] 

        # Loop through channels
        for count, container in enumerate(annotation_containers):

            # Channe label
            countbox = QLabel(f'#{count+1}')
            countbox.setAlignment(QtCore.Qt.AlignRight)
            countbox.setFixedWidth(len('#1')*8)            

            # Channe label
            labelbox = QLineEdit(f'{container.label}')
            labelbox.setAlignment(QtCore.Qt.AlignRight)
            labelbox.setFixedWidth(max(len(container.label) for container in annotation_containers)*16)

            ## Color in RGB
            #colorbox = QLineEdit(f'{container.facecolor}')
            #colorbox.setAlignment(QtCore.Qt.AlignRight)
            #colorbox.setFixedWidth(max(len(str(container.facecolor)) for container in annotation_containers)*8)
            #colorbox.setStyleSheet("background-color: {}".format(container.facecolor))
            
            # Set the background color
            palette = labelbox.palette()
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor(*container.facecolor))
            labelbox.setPalette(palette)           

            # Annotation color
            colorpick = QPushButton("Change color")
            colorpick.clicked.connect(self.pick_color)            

            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(countbox)
            row_layout.addWidget(labelbox)
            #row_layout.addWidget(colorpick)
            form_layout.addRow(row_layout)

            # Append  
            self.countbox.append(countbox)
            self.labelbox.append(labelbox)
            self.colorpick.append(colorpick)

        layout.addLayout(form_layout)

    def pick_color(self):
        color = QColorDialog.getColor()
        rgb   = (color.red(), color.green(), color.blue())
        index = self.colorpick.index(self.sender())

        # Set the background color
        palette = self.labelbox[index].palette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(*rgb))
        self.labelbox[index].setPalette(palette) 

        self.changesMade.emit()



class options(QtWidgets.QDialog):
    changesMade = QtCore.pyqtSignal()
    def __init__(self, exntensions, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()        
        self.extensions = []

        # Loop through EEG extensions
        labels = ['EEG extension left', 'EEG extension right']
        for count, label in enumerate(labels):

            # EEG extension
            labelbox = QLabel(label)
            labelbox.setAlignment(QtCore.Qt.AlignRight)        
            labelbox.setFixedWidth(max(len(label) for label in labels)*8)


            # Value by which EEG is extended
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setValue(exntensions[count])
            spinbox.setSuffix(" s") 
            spinbox.setDecimals(0)
            spinbox.valueChanged.connect(self.emit_signal)      

            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)
            row_layout.addWidget(spinbox)
            form_layout.addRow(row_layout)

            # append 
            self.extensions.append(spinbox)     
        layout.addLayout(form_layout)

    def get_extensions(self):
        ext_l = self.extensions[0].value()
        ext_r = self.extensions[1].value()
        return ext_l, ext_r

    def emit_signal(self):
        self.changesMade.emit()       




class scaleDialogeBox(QtWidgets.QDialog):
    changesMade = QtCore.pyqtSignal()

    def __init__(self, chaninfos, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.chaninfo = chaninfos
        self.scale      = []
        self.display    = []
        self.color      = []

        # Loop through channels
        for count, chaninfo in enumerate(self.chaninfo):

            # Channe label
            labelbox = QLabel(chaninfo['Channel'])
            labelbox.setAlignment(QtCore.Qt.AlignRight)
            labelbox.setFixedWidth(max(len(chaninfo['Channel']) for chaninfo in self.chaninfo)*8)

            # Value by which EEG is multiplied
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setValue(chaninfo['Scale'])
            spinbox.valueChanged.connect(self.emit_signal)  

            # Whether channel is displayed or not
            checkbox = QCheckBox(self)
            checkbox.setChecked(chaninfo['Display']) 
            checkbox.clicked.connect(self.emit_signal)

            # Channel color
            colorbox = QComboBox(self)
            colorbox.addItem("Black")
            colorbox.addItem("Blue")
            colorbox.addItem("Magenta")
            colorbox.setCurrentText(chaninfo['Color'])
            colorbox.currentIndexChanged.connect(self.emit_signal)

            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(spinbox)
            row_layout.addWidget(colorbox)
            form_layout.addRow(row_layout)

            self.scale.append(spinbox) # append  
            self.display.append(checkbox)
            self.color.append(colorbox)

        layout.addLayout(form_layout)

    def emit_signal(self):
        for counter, chaninfo in enumerate(self.chaninfo):
            chaninfo['Color']   = self.color[counter].currentText()
            chaninfo['Display'] = self.display[counter].isChecked()
            chaninfo['Scale']   = self.scale[counter].value()
        self.changesMade.emit()

    
