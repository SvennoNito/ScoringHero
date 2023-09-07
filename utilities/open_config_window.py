from widgets import ConfigurationWindow
from utilities.redraw_gui import redraw_gui
from data_handling.write_config import write_configuration_file
from signal_processing.build_times_vector import build_times_vector
from signal_processing.compute_spectogram import freqsOI_ui, spectogram_to_ui
from data_handling.cache import ui_to_cache, write_cache
from data_handling.write_scoring import write_scoring_wrapper


def open_config_window(ui):
    allow_staging = all([stage['stage'] == None for stage in ui.stages])
    ui.ConfigurationWindow = ConfigurationWindow(ui.config, ui.AnnotationContainer, allow_staging)
    ui.ChannelPage, ui.GeneralPage, ui.EventPage = ui.ConfigurationWindow.return_page()
    ui.ChannelPage.changesMade.connect(lambda: redraw_gui(ui))
    ui.GeneralPage.changesMade.connect(lambda config_parameter_name, ui=ui: apply_general_configurations(config_parameter_name, ui))
    ui.EventPage.changesMade.connect(lambda: event_page(ui))
    ui.ConfigurationWindow.finished.connect(lambda: apply_config_changes(ui))
    ui.ConfigurationWindow.show()        


def event_page(ui):
    write_scoring_wrapper(ui)


def apply_general_configurations(config_parameter_name, ui):

    if config_parameter_name == 'Channel_for_spectogram':
        spectogram_to_ui(ui)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)   
        write_cache(ui, ui_to_cache(ui))

    if config_parameter_name == 'Spectogram_limit_hz':
        ui.freqsOI = freqsOI_ui(ui.freqs, ui.config)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)    
        write_cache(ui, ui_to_cache(ui))

    apply_config_changes(ui)


def apply_config_changes(ui):

    # Build times vector
    build_times_vector(ui)

    # Redraw EEG
    redraw_gui(ui)

    # Write configuration file
    write_configuration_file(f'{ui.filename}.config.json', ui.config)