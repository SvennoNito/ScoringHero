import pyqtgraph as pg
import numpy as np
from .merge_borders import merge_borders
from .associated_epoch import associated_epoch
from paint_event.convert_to_seconds import convert_to_seconds

def draw_box(box_index, ui):

    # Compute rectangle size in seconds and microvolt
    converted_corners, converted_shape = convert_to_seconds(
        ui, ui.PaintEventWidget.stored_corners
    )    

    # Extract respective container
    container = ui.AnnotationContainer[box_index]

    # Assign corners to respective annotation box
    try:
        container.borders = container.borders.tolist()
    except:
        1
    [container.borders.append((corner[0].x(), corner[1].x())) for corner in converted_corners]
    
    # Merge borders
    container.borders = merge_borders(container.borders)

    # Associated epoch of each border
    container.epochs = associated_epoch(container.borders, ui.config[0]["Epoch_length_s"])

    # Epochs in this epoch
    box_in_this_epoch = [True if ui.this_epoch in epoch else False for epoch in container.epochs]
    
    # Remove all items
    [ui.SignalWidget.axes.removeItem(item) for item in container.drawn_boxes]

    # Draw rectangle
    # previously_drawn_borders = [item.getRegion() for item in container.drawn_boxes]
    container.drawn_boxes = []
    for border in container.borders[box_in_this_epoch]:
        box_to_be_drawn = pg.LinearRegionItem(brush=container.facecolor, pen=pg.mkPen(color=(0, 0, 0), width=2))
        box_to_be_drawn.setRegion([border[0], border[1]])   
        ui.SignalWidget.axes.addItem(box_to_be_drawn)   
        # if tuple(border) not in previously_drawn_borders:
        container.drawn_boxes.append(box_to_be_drawn)

    # Update paint evenet
    ui.PaintEventWidget.reset()
    ui.SignalWidget.text_period.setText("")
    ui.SignalWidget.text_amplitude.setText("")

