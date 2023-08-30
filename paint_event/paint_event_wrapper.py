from .convert_to_seconds import *
from .compute_total_length import *
from .drop_clicked_rectangle import *
from .show_rectangle_size import *
from .rectangle_power import *
from .order_corners import order_corners

def paint_event_wrapper(ui):
    # Correct for drawing rectangles from right to left
    if len(ui.PaintEventWidget.stored_corners) > 0:
        order_corners(ui.PaintEventWidget.stored_corners[-1])

        # Compute rectangle size in seconds and microvolt
        converted_corners, converted_shape = convert_to_seconds(
            ui, ui.PaintEventWidget.stored_corners
        )

        # Drop rectangle if clicked on
        if len(converted_shape) > 0:
            (   ui.PaintEventWidget.stored_corners,
                converted_corners,
                converted_shape,
            ) = drop_clicked_rectangle(
                ui, converted_corners, converted_shape
            )

            # Display total length of rectangles
            total_length = compute_total_length(converted_shape)
            ui.PaintEventWidget.length_text.setText(f"Total Length: {round(total_length, 2)} s")

            # Display length and amplitude of rectangles
            show_rectangle_size(ui, converted_corners, converted_shape)

            # Compute power
            if len(converted_corners) > 0:
                freqs, power = rectangle_power(ui, converted_corners[-1], converted_shape[-1])
                ui.RectanglePower.update_powerline(freqs, power)
