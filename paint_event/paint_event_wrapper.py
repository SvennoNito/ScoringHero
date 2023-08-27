from .convert_to_seconds import *
from .compute_total_length import *
from .drop_clicked_rectangle import *

def paint_event_wrapper(ui):
    rectangle_sizes   = convert_to_seconds(ui, ui.PaintEventWidget.stored_corners)
    ui.PaintEventWidget.stored_corners, rectangle_sizes = drop_clicked_rectangle(ui.PaintEventWidget.stored_corners, rectangle_sizes)
    total_length      = compute_total_length(rectangle_sizes)
    ui.PaintEventWidget.length_text.setText(f"Total Length: {round(total_length, 2)} s")
