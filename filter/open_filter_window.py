from widgets import FilterWindow
from utilities.redraw_gui import redraw_all
from config.write_configuration import save_configuration
from eeg.rebuild_display import rebuild_eeg_data_display
from signal_processing.recompute_derived import recompute_derived
from utilities.busy_indicator import run_busy


def open_filter_window(ui):
    if not hasattr(ui, "FilterWindow") or ui.FilterWindow is None:
        ui.FilterWindow = FilterWindow(
            ui.config[1],
            ui.config[0]["Sampling_rate_hz"],
        )
        ui.FilterWindow.load_settings(ui.config[1])
        ui.FilterWindow.filterApplied.connect(lambda: _after_filter(ui))
    ui.FilterWindow.show()
    ui.FilterWindow.raise_()


def _after_filter(ui):
    """The filter window has stored its settings on ui.config[1]: save and refilter."""
    save_configuration(ui)

    def work():
        rebuild_eeg_data_display(ui)
        recompute_derived(ui)

    run_busy(ui, "Filtering…", work, lambda _: redraw_all(ui))
