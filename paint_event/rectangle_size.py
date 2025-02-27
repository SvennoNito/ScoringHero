from signal_processing.sample_from_selection import sample_from_selection
from signal_processing.channel_from_selection import channel_from_selection
import numpy as np

def rectangle_size(ui, eeg_in_rectangle, channel, converted_corners, converted_shape):
    if len(converted_shape) > 0:


        # Amplitude text box
        text = f"{round(converted_shape[-1][1], 1)} \u03BCV"

        corner = converted_corners[-1]
        xposition = corner[0].x()
        yposition = min(corner[0].y(), corner[1].y())

        ui.SignalWidget.text_amplitude_box.setPos(xposition, yposition)
        ui.SignalWidget.text_amplitude_box.setText(text)


        # Amplitude peak-2-peak
        text = f"{max(eeg_in_rectangle) - min(eeg_in_rectangle):.1f} \u03BCV"

        corner = converted_corners[-1]
        xposition = corner[0].x()
        yposition = max(corner[0].y(), corner[1].y())

        ui.SignalWidget.text_amplitude_signal.setPos(xposition, yposition)
        ui.SignalWidget.text_amplitude_signal.setText(text)
        ui.SignalWidget.text_amplitude_signal.setColor(ui.config[1][channel]["Channel_color"])

        # Period length
        text = f"{round(converted_shape[-1][0], 2)} s"

        corner = converted_corners[-1]
        xposition = corner[0].x()
        yposition = min(corner[0].y(), corner[1].y())

        ui.SignalWidget.text_period.setPos(xposition, yposition)
        ui.SignalWidget.text_period.setText(text)

    else:
        # Reset text when there are no rectangles present
        ui.SignalWidget.text_amplitude_box.setText("")
        ui.SignalWidget.text_amplitude_signal.setText("")
        ui.SignalWidget.text_period.setText("")
