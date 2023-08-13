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


    def include(self, greenLines, EEG):
        whole_epoch     = greenLines.axes.getAxis('bottom').range # epoch range
        current_epoch   = [round(whole_epoch[0] + EEG.return_extension()[0]), round(whole_epoch[1] - EEG.return_extension()[0])]
        areas_in_screen = [item[0] >= whole_epoch[0] and item[1] <= whole_epoch[1] for item in self.borders]                        # Find areas that are entirely within the screen
        epoch_in_list   = [item[0] <= current_epoch[0] and item[1] >= current_epoch[1] for item in self.borders]                      # Find out whether the current epoch is part of a pervious area in list

        # Check if new green areas exist
        if len(greenLines.storedLines) > 0: 
            self.add_area(greenLines)

        else: # No new green areas
            if any(areas_in_screen):
                # Remove plotted areas on screen
                self.remove_areas_in_screen(areas_in_screen)
            elif any(epoch_in_list):
                # Remove current epoch that is part of one area in list
                self.remove_epoch_from_merged_area(current_epoch)
            else:
                # Epoch not yet in list
                self.borders.append(current_epoch)
                
            
        # Sanity check
        self.borders.sort(key=lambda x: x[0])
        self.merge_border()     # Merge overlapping borders
        self.related_epoch()    # Check which epochs are clean

        # Refresh plot
        self.erase_plotted_areas(greenLines)
        self.show_areas(greenLines)
        self.remove_green_areas(greenLines)
        # self.borders = self.remove_epoch_from_merged_area(current_epoch)


    def remove_areas_in_screen(self, areas_in_screen):       
        if any(areas_in_screen): 
            # Remove areas that are within the screen
            for index in np.where(areas_in_screen)[0][::-1]:
                self.borders.remove(self.borders[index])


    def remove_epoch_from_merged_area(self, current_epoch):
        start, end  = current_epoch
        result      = []
        
        for interval in self.borders:
            if interval[1] <= start or interval[0] >= end:
                # No overlap, keep the interval as it is
                result.append(interval)
            elif interval[0] < start and interval[1] > end:
                # Interval completely contains the current_epoch, split it into two
                result.append([interval[0], start])
                result.append([end, interval[1]])
            elif interval[0] < start and interval[1] <= end:
                # Interval overlaps with the left side of current_epoch
                result.append([interval[0], start])
            elif interval[0] >= start and interval[1] > end:
                # Interval overlaps with the right side of current_epoch
                result.append([end, interval[1]])
            elif interval == current_epoch:
                result.append(interval)
        self.borders = result


    def add_area(self, greenLines):
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
        else: # No new artefacts
            for item in newArtefacts: # Remove all artefacts
                self.borders.remove(item)

    def merge_border(self):
        merged_borders = []
        for start, end in self.borders:
            if not merged_borders or start >= merged_borders[-1][1]: # Add area if the start of the border is behind the end of the next border
                merged_borders.append([start, end])
            else:
                merged_borders[-1][1] = max(merged_borders[-1][1], end)
        self.borders = merged_borders        

    def remove_green_areas(self, greenLines):
        greenLines.reset()
        greenLines.update()          

    def related_epoch(self):
        epochs = []
        for border in self.borders:
            start, stop = border
            while stop - start > self.epolen:
                epochs.append(int(np.ceil(start / self.epolen) + 1))
                start += self.epolen
            epochs.append(int(np.ceil(stop / self.epolen)))                
        self.epoch = list(set(epochs))
            

    def add_instance(self, borders):
        for border in borders:
            self.border.append([border[0], border[1]])  

    def erase_plotted_areas(self, AxesEEG):
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
            labelbox = QLabel(chaninfo['Channel_name'])
            labelbox.setAlignment(QtCore.Qt.AlignRight)
            labelbox.setFixedWidth(max(len(chaninfo['Channel_name']) for chaninfo in self.chaninfo)*8)

            # Value by which EEG is multiplied
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setValue(chaninfo['Scaling_factor'])
            spinbox.valueChanged.connect(self.emit_signal)  

            # Whether channel is displayed or not
            checkbox = QCheckBox(self)
            checkbox.setChecked(chaninfo['Display_on_screen']) 
            checkbox.clicked.connect(self.emit_signal)

            # Channel color
            colorbox = QComboBox(self)
            colorbox.addItem("Black")
            colorbox.addItem("Blue")
            colorbox.addItem("Magenta")
            colorbox.setCurrentText(chaninfo['Channel_color'])
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
            chaninfo['Channel_color']       = self.color[counter].currentText()
            chaninfo['Display_on_screen']   = self.display[counter].isChecked()
            chaninfo['Scaling_factor']      = self.scale[counter].value()
        self.changesMade.emit()

    
class configuration_box(QtWidgets.QDialog):
    changesMade = QtCore.pyqtSignal()
    def __init__(self, configuration, parent=None):
        super().__init__(parent)
        layout              = QVBoxLayout(self)
        form_layout         = QFormLayout()      
        self.labels         = []  
        self.spinboxes      = []
        self.configuration  = configuration

        # Loop through configuration items
        for count, item in enumerate(configuration.items()):

            # EEG extension
            labelbox = QLabel(item[0])
            labelbox.setAlignment(QtCore.Qt.AlignRight)        
            labelbox.setFixedWidth(max(len(label) for label in configuration.keys())*8)

            # Value by which EEG is extended
            spinbox = QDoubleSpinBox(self)
            spinbox.setMinimum(0)
            spinbox.setMaximum(10000)
            spinbox.setValue(item[1])
            #spinbox.setSuffix(" s") 
            spinbox.setDecimals(0)
            spinbox.valueChanged.connect(self.emit_signal)

            # Layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(labelbox)
            row_layout.addWidget(spinbox)
            form_layout.addRow(row_layout)

            # append 
            self.labels.append(item[0]) 
            self.spinboxes.append(spinbox)     
        layout.addLayout(form_layout)

    def emit_signal(self):
        for (label, item) in zip(self.labels, self.spinboxes):
            self.configuration[label] = int(item.value())           
        self.changesMade.emit()       