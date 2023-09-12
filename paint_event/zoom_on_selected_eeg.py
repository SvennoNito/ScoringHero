import matplotlib.pyplot as plt
from .selected_samples import selected_samples
from .selected_channel import selected_channel


def zoom_on_selected_eeg(ui):
    data, times = ui.PaintEventWidget.selected_data
    times -= times[0]

    if hasattr(ui, "figure_zoom"):
        if plt.fignum_exists(ui.figure_zoom.number):
            lines = ui.figure_zoom.get_axes()[0].lines
            plt.close(ui.figure_zoom)
            ui.figure_zoom, ax = plt.subplots()
            for line in lines:
                ax.plot(line.get_xdata(), line.get_ydata())

        else:
            ui.figure_zoom, ax = plt.subplots()
    else:
        ui.figure_zoom, ax = plt.subplots()

    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Amplitude \u03BCV")
    ax.plot(times, data)
    plt.show()
