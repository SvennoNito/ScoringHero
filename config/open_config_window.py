from widgets import ConfigurationWindow
from utilities.redraw_gui import redraw_gui
from data_handling.write_scoring import write_scoring_catch_error
from .apply_changes import apply_changes

def open_config_window(ui):
    allow_staging = all([stage['stage'] == None for stage in ui.stages])
    
    ui.ConfigurationWindow = ConfigurationWindow(ui.config, ui.AnnotationContainer, allow_staging)
    ui.ChannelPage, ui.GeneralPage, ui.EventPage = ui.ConfigurationWindow.return_page()
    ui.ChannelPage.changesMade.connect(lambda: redraw_gui(ui))
    ui.GeneralPage.changesMade.connect(lambda config_parameter_name, ui=ui: apply_changes(config_parameter_name, ui))
    ui.EventPage.changesMade.connect(lambda: write_scoring_catch_error(ui))
    #ui.ConfigurationWindow.finished.connect(lambda: apply_config_changes(ui))
    ui.ConfigurationWindow.show()        

