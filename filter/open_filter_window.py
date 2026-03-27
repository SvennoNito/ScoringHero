from widgets import FilterWindow
from utilities.redraw_gui import redraw_gui
from filter.apply_filter import apply_filter


def open_filter_window(ui):
    ui.FilterWindow = FilterWindow(
        ui.config[1],
        ui.config[0]["Sampling_rate_hz"],
    )
    ui.FilterWindow.filterApplied.connect(lambda settings: _after_filter(ui, settings))
    ui.FilterWindow.show()


def _after_filter(ui, filter_settings):
    ui.eeg_data_display = apply_filter(ui.eeg_data, ui.config[0]["Sampling_rate_hz"], filter_settings)
    redraw_gui(ui)
