from widgets import ConfigurationWindow
from utilities.redraw_gui import redraw_gui
from scoring.write_scoring import write_scoring
from .apply_changes import apply_changes
from .write_configuration import write_configuration

def _move_eeg_row(ui, from_idx, to_idx):
    """Reindex eeg_data and eeg_data_display after a channel drag-reorder.

    This is a lightweight alternative to apply_changes: no filters are re-applied
    and no spectrograms are recomputed. The display data is still valid — each
    channel's processed signal moves with its config entry — so we just reindex
    both arrays and redraw.
    """
    order = list(range(ui.eeg_data.shape[0]))
    order.pop(from_idx)
    order.insert(to_idx, from_idx)
    ui.eeg_data = ui.eeg_data[order]
    ui.eeg_data_display = ui.eeg_data_display[order]
    redraw_gui(ui)
    write_configuration(f"{ui.filename}.config.json", ui.config)


def open_config_window(ui):
    allow_staging = all([stage["stage"] == None for stage in ui.stages])

    channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
    ui.ConfigurationWindow = ConfigurationWindow(ui.config, ui.AnnotationContainer, allow_staging, channel_labels)
    ui.ChannelPage, ui.GeneralPage, ui.EventPage, ui.WaveletPage, ui.SpectrogramPage, ui.PeriodogramPage = ui.ConfigurationWindow.return_page()
    ui.ChannelPage.channelMoved.connect(lambda f, t, ui=ui: _move_eeg_row(ui, f, t))
    ui.ChannelPage.changesMade.connect(lambda: apply_changes([], ui))
    ui.GeneralPage.changesMade.connect(
        lambda config_parameter_name, ui=ui: apply_changes(config_parameter_name, ui)
    )
    ui.WaveletPage.changesMade.connect(
        lambda config_parameter_name, ui=ui: apply_changes(config_parameter_name, ui)
    )
    ui.SpectrogramPage.changesMade.connect(
        lambda config_parameter_name, ui=ui: apply_changes(config_parameter_name, ui)
    )
    ui.PeriodogramPage.changesMade.connect(
        lambda config_parameter_name, ui=ui: apply_changes(config_parameter_name, ui)
    )
    ui.EventPage.changesMade.connect(lambda: write_scoring(ui))
    # ui.ConfigurationWindow.finished.connect(lambda: write_configuration(f"{ui.filename}.config.json", ui.config))
    ui.ConfigurationWindow.show()
