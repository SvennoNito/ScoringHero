from widgets import ConfigurationWindow
from utilities.redraw_gui import redraw_gui
from scoring.write_scoring import write_scoring
from .apply_changes import apply_changes
from .write_configuration import write_configuration

def open_config_window(ui):
    allow_staging = all([stage["stage"] == None for stage in ui.stages])

    ui.ConfigurationWindow = ConfigurationWindow(ui.config, ui.AnnotationContainer, allow_staging)
    ui.ChannelPage, ui.GeneralPage, ui.EventPage = ui.ConfigurationWindow.return_page()
    ui.ChannelPage.changesMade.connect(lambda: apply_changes([], ui))
    ui.GeneralPage.changesMade.connect(
        lambda config_parameter_name, ui=ui: apply_changes(config_parameter_name, ui)
    )
    ui.EventPage.changesMade.connect(lambda: write_scoring(ui))
    # ui.ConfigurationWindow.finished.connect(lambda: write_configuration(f"{ui.filename}.config.json", ui.config))
    ui.ConfigurationWindow.show()
