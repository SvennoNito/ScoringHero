from widgets import FilterWindow
from utilities.redraw_gui import redraw_gui
from config.write_configuration import write_configuration
from eeg.rebuild_display import rebuild_eeg_data_display
from signal_processing.recompute_derived import recompute_derived


def open_filter_window(ui):
    if not hasattr(ui, "FilterWindow") or ui.FilterWindow is None:
        ui.FilterWindow = FilterWindow(
            ui.config[1],
            ui.config[0]["Sampling_rate_hz"],
        )
        ui.FilterWindow.load_settings(ui.config[1])
        ui.FilterWindow.filterApplied.connect(lambda settings: _after_filter(ui, settings))
    ui.FilterWindow.show()
    ui.FilterWindow.raise_()


def _after_filter(ui, filter_settings):
    for i, settings in enumerate(filter_settings):
        ui.config[1][i]["Filter_hp_enabled"]    = settings["hp_enabled"]
        ui.config[1][i]["Filter_hp_cutoff"]      = settings["hp_cutoff"]
        ui.config[1][i]["Filter_hp_order"]        = settings["hp_order"]
        ui.config[1][i]["Filter_lp_enabled"]      = settings["lp_enabled"]
        ui.config[1][i]["Filter_lp_cutoff"]        = settings["lp_cutoff"]
        ui.config[1][i]["Filter_lp_order"]          = settings["lp_order"]
        ui.config[1][i]["Filter_notch_enabled"]    = settings["notch_enabled"]
        ui.config[1][i]["Filter_notch_cutoff"]      = settings["notch_cutoff"]
        ui.config[1][i]["Filter_notch_order"]        = settings["notch_order"]
    write_configuration(f"{ui.filename}.config.json", ui.config)

    rebuild_eeg_data_display(ui)
    recompute_derived(ui)
    redraw_gui(ui)
