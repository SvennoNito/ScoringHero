def convert_to_seconds(ui, stored_corners):

    shape = []
    for corner in stored_corners:
        width   = abs(ui.SignalWidget.axes.plotItem.vb.mapSceneToView(corner[1]).x() - ui.SignalWidget.axes.plotItem.vb.mapSceneToView(corner[0]).x())
        height  = abs(ui.SignalWidget.axes.plotItem.vb.mapSceneToView(corner[1]).y() - ui.SignalWidget.axes.plotItem.vb.mapSceneToView(corner[0]).y())
        shape.append((width, height))

    return shape
