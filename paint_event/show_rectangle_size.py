import pyqtgraph as pg
from PySide6.QtGui import QFont


def show_rectangle_size(ui, converted_corners, converted_shape):
    if len(converted_shape) > 0:
        # Amplitude
        text = f"{round(converted_shape[-1][1], 2)} \u03BCV"

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
