import numpy as np
import pyqtgraph as pg

def draw_box_in_epoch(ui, container):

    # Epochs in this epoch
    box_in_this_epoch = [True if (ui.this_epoch in epoch) | (ui.this_epoch+1 in epoch) else False for epoch in container.epochs]
    
    # Remove all items
    [ui.SignalWidget.axes.removeItem(item) for item in container.drawn_boxes]

    # Draw rectangle
    # previously_drawn_borders = [item.getRegion() for item in container.drawn_boxes]
    container.drawn_boxes = []
    for border in np.array(container.borders)[box_in_this_epoch]:
        box_to_be_drawn = pg.LinearRegionItem(brush=container.facecolor, pen=pg.mkPen(color=(0, 0, 0), width=3))
        box_to_be_drawn.setRegion([border[0], border[1]])   
        ui.SignalWidget.axes.addItem(box_to_be_drawn)   
        # if tuple(border) not in previously_drawn_borders:
        container.drawn_boxes.append(box_to_be_drawn)