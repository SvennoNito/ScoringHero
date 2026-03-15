import pyqtgraph as pg

LINE_COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#e377c2", "#8c564b", "#17becf", "#ff7f0e"]
LINE_WIDTH = 4


def zoom_on_selected_eeg(ui):
    data, times = ui.PaintEventWidget.selected_data
    times = times - times[0]

    prev_lines = []
    if hasattr(ui, "figure_zoom") and ui.figure_zoom is not None:
        try:
            if ui.figure_zoom.isVisible():
                for item in ui.figure_zoom.getPlotItem().listDataItems():
                    prev_lines.append((item.xData.copy(), item.yData.copy()))
            ui.figure_zoom.close()
        except RuntimeError:
            pass

    win = pg.PlotWidget(title="Selected EEG")
    win.setBackground("w")

    axis_pen = pg.mkPen(color="k", width=1)
    for axis_name in ["bottom", "left", "top", "right"]:
        axis = win.getPlotItem().getAxis(axis_name)
        axis.setPen(axis_pen)
        axis.setTextPen(axis_pen)

    win.setLabel("bottom", "Time (seconds)", color="k")
    win.setLabel("left", "Amplitude \u03BCV", color="k")

    all_lines = prev_lines + [(times, data)]
    for i, (x, y) in enumerate(all_lines):
        color = LINE_COLORS[i % len(LINE_COLORS)]
        win.plot(x, y, pen=pg.mkPen(color=color, width=LINE_WIDTH))

    win.show()
    ui.figure_zoom = win
