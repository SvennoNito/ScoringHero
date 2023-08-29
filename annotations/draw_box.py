import pyqtgraph as pg
from paint_event.convert_to_seconds import convert_to_seconds

def draw_box(box_index, ui):

    # Compute rectangle size in seconds and microvolt
    converted_corners, converted_shape = convert_to_seconds(
        ui, ui.PaintEventWidget.stored_corners
    )    

    # Assign corners to respective annotation box
    new_borders = [(corner[0].x(), corner[1].x()) for corner in converted_corners]
    [ui.AnnotationContainer[box_index].borders.append(border) for border in new_borders]

    # Draw rectangle
    for border in new_borders:
        box_to_be_drawn = pg.LinearRegionItem(brush=ui.AnnotationContainer[box_index].facecolor, pen=pg.mkPen(color=(0, 0, 0), width=2))
        box_to_be_drawn.setRegion([border[0], border[1]]) 
        #if tuple(border) not in previous_areas:     
        ui.SignalWidget.axes.addItem(box_to_be_drawn)      

    # Update paint evenet
    ui.PaintEventWidget.reset()
    ui.SignalWidget.text_period.setText("")
    ui.SignalWidget.text_amplitude.setText("")

