def convert_to_seconds(ui, stored_corners):
    converted_corners = []
    converted_shape = []
    for corner in stored_corners:
        # Rectangle corner conerted to time and amplitude unit
        converted_corners.append(ui.SignalWidget.axes.plotItem.vb.mapSceneToView(corner))

        # Width and height of rectangle in seconds and microvolt
        width = abs(converted_corners[-1][1].x() - converted_corners[-1][0].x())
        height = abs(converted_corners[-1][1].y() - converted_corners[-1][0].y())
        converted_shape.append((width, height))

    return converted_corners, converted_shape
