import pyqtgraph as pg
import numpy as np
from PyQt5.QtCore import QPoint
from .merge_borders import merge_borders
from .associated_epoch import associated_epoch
from .draw_box_in_epoch import draw_box_in_epoch
from .remove_epoch_from_merged_area import remove_epoch_from_merged_area
from paint_event.convert_to_seconds import convert_to_seconds
from data_handling.write_scoring import write_scoring_wrapper

def draw_box(box_index, ui):

    # Extract respective container
    container = ui.AnnotationContainer[box_index]    

    # Compute rectangle size in seconds and microvolt
    converted_corners, _ = convert_to_seconds(
        ui, ui.PaintEventWidget.stored_corners
    )    


    if len(converted_corners) == 0:        
        # No rectangle was drawn
        converted_corners = [
            ui.this_epoch*ui.config[0]['Epoch_length_s'],
            (ui.this_epoch+1)*ui.config[0]['Epoch_length_s']
        ]

        # Append or remove epoch
        container.borders = remove_epoch_from_merged_area(container.borders, converted_corners)
        if converted_corners not in container.borders:
            container.borders.append(converted_corners)
        else:
            container.borders.remove(converted_corners)        

    else:
        # Rectangle was drawn
        [container.borders.append([corner[0].x(), corner[1].x()]) for corner in converted_corners]
    
    # Merge borders
    container.borders = merge_borders(container.borders)

    # Associated epoch of each border
    container.epochs = associated_epoch(container.borders, ui.config[0]["Epoch_length_s"])

    # Draw rectangle
    draw_box_in_epoch(ui, container)

    # Update paint evenet
    ui.PaintEventWidget.reset()
    ui.SignalWidget.text_period.setText("")
    ui.SignalWidget.text_amplitude.setText("")

    # Write scoring file
    write_scoring_wrapper(ui)        