from .convert_to_seconds import convert_to_seconds
from .total_length import total_length
from .drop_clicked_rectangle import drop_clicked_rectangle
from .rectangle_size import rectangle_size
from .order_by_time import order_by_time
from .eeg_from_rectangle import eeg_from_rectangle
from signal_processing.compute_periodogram import compute_periodogram



def paint_event_handler(ui):
    # Correct for drawing rectangles from right to left
    if len(ui.PaintEventWidget.stored_corners) > 0:
        order_by_time(ui.PaintEventWidget.stored_corners[-1])

        # Compute rectangle size in seconds and microvolt
        converted_corners, converted_shape = convert_to_seconds(
            ui, ui.PaintEventWidget.stored_corners
        )

        # Drop rectangle if clicked on
        if len(converted_shape) > 0:
            (
                ui.PaintEventWidget.stored_corners,
                converted_corners,
                converted_shape,
            ) = drop_clicked_rectangle(ui, converted_corners, converted_shape)

            # Display total length of rectangles
            total_length_value = total_length(converted_shape)
            ui.PaintEventWidget.length_text.setText(
                f"Total Length: {round(total_length_value, 2)} s"
            )

            # Selected EEG data 
            data, times = eeg_from_rectangle(ui, converted_corners, converted_shape)          

            # Display length and amplitude of rectangles
            rectangle_size(ui, data, converted_corners, converted_shape)

            # Compute power
            if len(converted_corners) > 0:
                freqs, power = compute_periodogram(ui, data, times)
                ui.RectanglePower.update_powerline(freqs, power)
