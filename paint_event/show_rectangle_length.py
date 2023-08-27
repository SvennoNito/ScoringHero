import pyqtgraph as pg
from PySide6.QtGui import QFont

def show_rectangle_length(ui, rectangle_sizes):

    if len(rectangle_sizes) > 0:
        text        = f'{round(rectangle_sizes[-1][0], 2)} s'

        corner      = ui.PaintEventWidget.stored_corners[-1]
        xposition   = ui.SignalWidget.axes.plotItem.vb.mapSceneToView(corner[1]).x() 
        yposition   = min(
            ui.SignalWidget.axes.plotItem.vb.mapSceneToView(corner[0]).y(),
            ui.SignalWidget.axes.plotItem.vb.mapSceneToView(corner[1]).y()
        ) 

        ui.SignalWidget.text_period.setPos(xposition, yposition)
        ui.SignalWidget.text_period.setText(text)

    else:
        # Reset text when there are no rectangles present
        ui.SignalWidget.text_period.setText('')    

