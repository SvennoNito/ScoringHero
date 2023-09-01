from widgets import ConfigurationWindow
from utilities.redraw_gui import redraw_gui
from data_handling.write_config import write_configuration_file

def open_config_window(ui):
    ui.ConfigurationWindow = ConfigurationWindow(ui.config)
    ui.ChannelPage = ui.ConfigurationWindow.return_channel_page()
    ui.ChannelPage.changesMade.connect(lambda: redraw_gui(ui))
    ui.ConfigurationWindow.finished.connect(lambda: write_configuration_file(f'{ui.filename}.config.json', ui.config))
    ui.ConfigurationWindow.show()        