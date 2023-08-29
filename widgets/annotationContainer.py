
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui, QtCore
from PyQt5.QtCore import QObject, pyqtSignal


class AnnotationContainer(QObject):
    changesMade = pyqtSignal()
    def __init__(self, colorindex=0, label='Artefact', parent=None):
        super().__init__(parent)

        self.colorpalette = [
            (255, 200, 200, 100), 
            (44, 160, 44, 100),
            (31, 119, 180, 100),
            (255, 127, 14, 100),
            (214, 39, 40, 100),
            (148, 103, 189, 100),
            (140, 86, 75, 100),
            (227, 119, 194, 100),
            (127, 127, 127, 100),
            (188, 189, 34, 100),
        ]

        self.facecolor      = self.colorpalette[colorindex]
        self.label          = label if not "F0" else "Artifacts"
        self.borders        = []
        self.drawn_boxes    = []
    #     self.borders    = []
    #     self.epoch      = []
    #     self.epolen     = epolen


    # def include(self, greenLines, EEG):
    #     whole_epoch     = greenLines.axes.getAxis('bottom').range # epoch range
    #     current_epoch   = [round(whole_epoch[0] + EEG.return_extension()[0]), round(whole_epoch[1] - EEG.return_extension()[0])]
    #     areas_in_screen = [item[0] >= whole_epoch[0] and item[1] <= whole_epoch[1] for item in self.borders]                        # Find areas that are entirely within the screen
    #     epoch_in_list   = [item[0] <= current_epoch[0] and item[1] >= current_epoch[1] for item in self.borders]                      # Find out whether the current epoch is part of a pervious area in list

    #     # Check if new green areas exist
    #     if len(greenLines.storedLines) > 0: 
    #         self.add_area(greenLines)

    #     else: # No new green areas
    #         if any(areas_in_screen):
    #             # Remove plotted areas on screen
    #             self.remove_areas_in_screen(areas_in_screen)
    #         elif any(epoch_in_list):
    #             # Remove current epoch that is part of one area in list
    #             self.remove_epoch_from_merged_area(current_epoch)
    #         else:
    #             # Epoch not yet in list
    #             self.borders.append(current_epoch)
                
            
    #     # Sanity check
    #     self.borders.sort(key=lambda x: x[0])
    #     self.merge_border()     # Merge overlapping borders
    #     self.related_epoch()    # Check which epochs are clean

    #     # Refresh plot
    #     self.erase_plotted_areas(greenLines)
    #     self.show_areas(greenLines)
    #     self.remove_green_areas(greenLines)
    #     # self.borders = self.remove_epoch_from_merged_area(current_epoch)


    # def remove_areas_in_screen(self, areas_in_screen):       
    #     if any(areas_in_screen): 
    #         # Remove areas that are within the screen
    #         for index in np.where(areas_in_screen)[0][::-1]:
    #             self.borders.remove(self.borders[index])


    # def remove_epoch_from_merged_area(self, current_epoch):
    #     start, end  = current_epoch
    #     result      = []
        
    #     for interval in self.borders:
    #         if interval[1] <= start or interval[0] >= end:
    #             # No overlap, keep the interval as it is
    #             result.append(interval)
    #         elif interval[0] < start and interval[1] > end:
    #             # Interval completely contains the current_epoch, split it into two
    #             result.append([interval[0], start])
    #             result.append([end, interval[1]])
    #         elif interval[0] < start and interval[1] <= end:
    #             # Interval overlaps with the left side of current_epoch
    #             result.append([interval[0], start])
    #         elif interval[0] >= start and interval[1] > end:
    #             # Interval overlaps with the right side of current_epoch
    #             result.append([end, interval[1]])
    #         elif interval == current_epoch:
    #             result.append(interval)
    #     self.borders = result


    # def add_area(self, greenLines):
    #     newArtefacts = []
    #     for line in greenLines.storedLines: # get all green lines
    #         newArtefacts.append([
    #             round(greenLines.axes.plotItem.vb.mapSceneToView(line[0]).x(),3),
    #             round(greenLines.axes.plotItem.vb.mapSceneToView(line[1]).x(),3)])
    #     newArtefacts = [item for item in newArtefacts if item[0] != item[1]] # Remove dublicates

    #     if not all(item in self.borders for item in newArtefacts): # If there are new artefacts
    #         for item in newArtefacts: # Store those new artefacts
    #             if item not in self.borders:
    #                 self.borders.append(item)
    #     else: # No new artefacts
    #         for item in newArtefacts: # Remove all artefacts
    #             self.borders.remove(item)

    # def merge_border(self):
    #     merged_borders = []
    #     for start, end in self.borders:
    #         if not merged_borders or start >= merged_borders[-1][1]: # Add area if the start of the border is behind the end of the next border
    #             merged_borders.append([start, end])
    #         else:
    #             merged_borders[-1][1] = max(merged_borders[-1][1], end)
    #     self.borders = merged_borders        

    # def remove_green_areas(self, greenLines):
    #     greenLines.reset()
    #     greenLines.update()          

    # def related_epoch(self):
    #     epochs = []
    #     for border in self.borders:
    #         start, stop = border
    #         while stop - start > self.epolen:
    #             epochs.append(int(np.ceil(start / self.epolen) + 1))
    #             start += self.epolen
    #         epochs.append(int(np.ceil(stop / self.epolen)))                
    #     self.epoch = list(set(epochs))
            

    # def add_instance(self, borders):
    #     for border in borders:
    #         self.border.append([border[0], border[1]])  

    # def erase_plotted_areas(self, AxesEEG):
    #     for item in AxesEEG.axes.items():
    #         if isinstance(item, pg.LinearRegionItem):
    #             rgb = item.brush.color()
    #             if self.facecolor == (rgb.red(), rgb.green(), rgb.blue(), rgb.alpha()):
    #                 AxesEEG.axes.removeItem(item)

    # def show_areas(self, AxesEEG):
    #     previous_areas  = [item.getRegion() for item in AxesEEG.axes.items() if isinstance(item, pg.LinearRegionItem)]
    #     for border in self.borders:
    #         red_area = pg.LinearRegionItem(brush=self.facecolor, pen=pg.mkPen(color=(0, 0, 0), width=2))
    #         red_area.setRegion([border[0], border[1]]) 
    #         if tuple(border) not in previous_areas:     
    #             AxesEEG.axes.addItem(red_area)   

    #     #for item in greenLines.axes.items(): # Remove all areas
    #     #    if isinstance(item, pg.LinearRegionItem):
    #     #        greenLines.axes.removeItem(item)                      