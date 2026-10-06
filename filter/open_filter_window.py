from widgets import FilterWindow
from eeg.displayed_signal import settings_changed


def open_filter_window(ui):
    if not hasattr(ui, "FilterWindow") or ui.FilterWindow is None:
        ui.FilterWindow = FilterWindow(
            ui.config[1],
            ui.config[0]["Sampling_rate_hz"],
        )
        ui.FilterWindow.load_settings(ui.config[1])
        # The filter window stores its settings on ui.config[1] before notifying
        ui.FilterWindow.filterApplied.connect(lambda: settings_changed(ui))
    ui.FilterWindow.show()
    ui.FilterWindow.raise_()
