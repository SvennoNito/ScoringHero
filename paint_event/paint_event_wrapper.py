from .convert_to_seconds import *
from .compute_total_length import *
from .drop_clicked_rectangle import *
from .show_rectangle_length import *
from .show_rectangle_height import *

def paint_event_wrapper(ui):

    # Compute rectangle size in seconds and microvolt
    rectangle_sizes = convert_to_seconds(ui, ui.PaintEventWidget.stored_corners)

    # Drop rectangle if clicked on
    if len(rectangle_sizes) > 0:
        ui.PaintEventWidget.stored_corners, rectangle_sizes = drop_clicked_rectangle(ui.PaintEventWidget.stored_corners, rectangle_sizes)
        
        # Display total length of rectangles
        total_length = compute_total_length(rectangle_sizes)
        ui.PaintEventWidget.length_text.setText(f"Total Length: {round(total_length, 2)} s")

        # Display length and amplitude of rectangles
        show_rectangle_length(ui, rectangle_sizes)
        show_rectangle_height(ui, rectangle_sizes)

