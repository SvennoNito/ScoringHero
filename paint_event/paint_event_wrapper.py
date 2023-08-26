from .convert_to_seconds import *
from .compute_total_length import *

def paint_event_wrapper(ui):
    ui.PaintEventWidget.shape_in_unit   = convert_to_seconds(ui, ui.PaintEventWidget.stored_corners)
    total_length                        = compute_total_length(ui.PaintEventWidget.shape_in_unit)
    ui.PaintEventWidget.length_text.setText(f"Total Length: {round(total_length, 2)} s")
