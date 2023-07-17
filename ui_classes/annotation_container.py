from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np

class annotation_container(QtCore.QObject):
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

    def add_instance(self, start, stop):
        self.border.append([start, stop])  

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