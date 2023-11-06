from signal_processing.sample_from_selection import sample_from_selection
from signal_processing.channel_from_selection import channel_from_selection
import numpy as np

def rectangle_size(ui, converted_corners, converted_shape):
    if len(converted_shape) > 0:

        # Selected sample points
        samples, times = sample_from_selection(ui.times, ui.this_epoch, converted_corners[-1])

        # Select channel
        channel = channel_from_selection(ui.config, converted_corners[-1], converted_shape[-1])

        # Compute power
        data    = ui.eeg_data[channel][samples]
        minmax  = max(data) - min(data)

        # Amplitude
        # text = f"{round(converted_shape[-1][1], 2)} \u03BCV"
        text = f"{minmax:.2f} \u03BCV"

        corner = converted_corners[-1]
        xposition = corner[0].x()
        yposition = max(corner[0].y(), corner[1].y())

        ui.SignalWidget.text_amplitude.setPos(xposition, yposition)
        ui.SignalWidget.text_amplitude.setText(text)

        # Period length
        text = f"{round(converted_shape[-1][0], 2)} s"

        corner = converted_corners[-1]
        xposition = corner[1].x()
        yposition = min(corner[0].y(), corner[1].y())

        ui.SignalWidget.text_period.setPos(xposition, yposition)
        ui.SignalWidget.text_period.setText(text)

    else:
        # Reset text when there are no rectangles present
        ui.SignalWidget.text_amplitude.setText("")
        ui.SignalWidget.text_period.setText("")
