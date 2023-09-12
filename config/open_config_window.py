from widgets import ConfigurationWindow
from utilities.redraw_gui import redraw_gui
from data_handling.write_config import write_configuration_file
from signal_processing.build_times_vector import build_times_vector
from signal_processing.compute_spectogram import freqsOI_ui, spectogram_to_ui
from data_handling.cache import ui_to_cache, write_cache
from data_handling.write_scoring import write_scoring_catch_error
from data_handling.load_eeg import compute_numepo
from data_handling.default_scoring import default_scoring
from signal_processing.trim_power import trim_power
from signal_processing.min_max_scale import min_max_scale


def open_config_window(ui):
    allow_staging = all([stage['stage'] == None for stage in ui.stages])
    ui.ConfigurationWindow = ConfigurationWindow(ui.config, ui.AnnotationContainer, allow_staging)
    ui.ChannelPage, ui.GeneralPage, ui.EventPage = ui.ConfigurationWindow.return_page()
    ui.ChannelPage.changesMade.connect(lambda: redraw_gui(ui))
    ui.GeneralPage.changesMade.connect(lambda config_parameter_name, ui=ui: apply_general_configurations(config_parameter_name, ui))
    ui.EventPage.changesMade.connect(lambda: event_page(ui))
    #ui.ConfigurationWindow.finished.connect(lambda: apply_config_changes(ui))
    ui.ConfigurationWindow.show()        


def event_page(ui):
    write_scoring_catch_error(ui)


def apply_general_configurations(config_parameter_name, ui):

    if ('Sampling_rate_hz' in config_parameter_name) or ('Epoch_length_s' in config_parameter_name):
        ui.numepo = compute_numepo(
                ui.eeg_data.shape[1],
                ui.config[0]["Sampling_rate_hz"],
                ui.config[0]["Epoch_length_s"],
            )        
        ui.stages = default_scoring(ui.config[0]["Epoch_length_s"], ui.numepo)

    if ('Sampling_rate_hz' in config_parameter_name) or ('Epoch_length_s' in config_parameter_name) or ('Extension_epoch_s' in config_parameter_name):        
        build_times_vector(ui)

    if ('Channel_for_spectogram' in config_parameter_name) or ('Sampling_rate_hz' in config_parameter_name) or ('Epoch_length_s' in config_parameter_name):
        spectogram_to_ui(ui)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)   
        write_cache(ui, ui_to_cache(ui))

    if 'Spectogram_limit_hz' in config_parameter_name:
        ui.freqsOI = freqsOI_ui(ui.freqs, ui.config)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)    
        write_cache(ui, ui_to_cache(ui))        

    if 'Periodogram_limit_hz' in config_parameter_name:
        power, freqs = trim_power(
            ui.power[ui.this_epoch],
            ui.freqs,
            ui.config[0]["Periodogram_limit_hz"][0],
            ui.config[0]["Periodogram_limit_hz"][1],
        )
        power = min_max_scale(power)
        ui.RectanglePower.update_powerline(freqs, power)             

    apply_config_changes(ui)


def apply_config_changes(ui):

    # Redraw EEG
    redraw_gui(ui)

    # Write configuration file
    write_configuration_file(f'{ui.filename}.config.json', ui.config)