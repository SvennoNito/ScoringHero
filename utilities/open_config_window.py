from widgets import ConfigurationWindow
from utilities.redraw_gui import redraw_gui
from data_handling.write_config import write_configuration_file
from signal_processing.build_times_vector import build_times_vector
from signal_processing.compute_spectogram import freqs_of_interest_indices


def open_config_window(ui):
    ui.ConfigurationWindow = ConfigurationWindow(ui.config)
    ui.ChannelPage, ui.GeneralPage = ui.ConfigurationWindow.return_page()
    ui.ChannelPage.changesMade.connect(lambda: redraw_gui(ui))
    # ui.GeneralPage.changesMade.connect(lambda: redraw_gui(ui))
    ui.ConfigurationWindow.finished.connect(lambda: apply_config_changes(ui))
    ui.ConfigurationWindow.show()        


def apply_config_changes(ui):

    # Build times vector
    build_times_vector(ui)

    # Spectogram borders
    ui.freqsOI = freqs_of_interest_indices(
        ui.freqs,
        ui.config[0]["Spectogram_lower_limit_hz"],
        ui.config[0]["Spectogram_upper_limit_hz"],
    )
    ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)

    # Redraw EEG
    redraw_gui(ui)

    # Write configuration file
    write_configuration_file(f'{ui.filename}.config.json', ui.config)