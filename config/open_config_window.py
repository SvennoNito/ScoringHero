from widgets import ConfigurationWindow
from eeg.displayed_signal import channel_renamed, settings_changed
from .apply_changes import apply_changes
from .channel_settings import ANALYSIS_CHANNEL_KEYS, derive_channel


def _rename_channel(ui, old_name, new_name):
    channel_renamed(ui, old_name, new_name)
    # Filter window caches the channel names in its row labels — rebuild it next
    # time it is opened so it shows the new ones.
    ui.FilterWindow = None


def _add_channel(ui, channel_a_name, channel_b_name):
    """Add a new derived channel (A − B), then refresh."""
    applied_keys = ui.ConfigurationWindow.resolve_pending()
    if applied_keys is None:
        return  # Cancel: keep the window and its pending edits
    ui.config[1].append(derive_channel(ui.config[1], channel_a_name, channel_b_name))

    # Build the new channel and refresh all widgets (incl. any just-applied settings)
    apply_changes(applied_keys, ui, channels_changed=True)

    # Reset filter window so it rebuilds with the new channel list next time
    ui.FilterWindow = None

    # Close the current config window and reopen on the Channels tab
    ui.ConfigurationWindow.close()
    open_config_window(ui)
    ui.ConfigurationWindow.tabs.setCurrentIndex(1)


def _delete_channel(ui, idx):
    """Remove channel at idx from the config, then refresh."""
    applied_keys = ui.ConfigurationWindow.resolve_pending()
    if applied_keys is None:
        return  # Cancel: keep the window and its pending edits
    del_name = ui.config[1][idx]["Channel_name"]
    ui.config[1].pop(idx)

    # Clear any re-reference that pointed to the deleted channel
    for ch in ui.config[1]:
        if ch["Re_reference"] == del_name:
            ch["Re_reference"] = "None"

    # Update spectrogram/wavelet/periodogram channel selectors if needed
    remaining_names = [c["Channel_name"] for c in ui.config[1]]
    fallback = remaining_names[0] if remaining_names else ""
    for key in ANALYSIS_CHANNEL_KEYS:
        if ui.config[0].get(key) == del_name:
            ui.config[0][key] = fallback

    # Drop the row, rebuild re-referenced rows and refresh (incl. any just-applied settings)
    apply_changes(applied_keys, ui, channels_changed=True)

    # Reset filter window so it rebuilds with the updated channel list next time
    ui.FilterWindow = None

    # Close the current config window and reopen on the Channels tab
    ui.ConfigurationWindow.close()
    open_config_window(ui)
    ui.ConfigurationWindow.tabs.setCurrentIndex(1)


def _delete_event(ui, idx):
    ui.edit_events(lambda events: events.clear(idx))


def open_config_window(ui):
    allow_staging = all(stage is None for stage in ui.scoring.stages())

    channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
    ui.ConfigurationWindow = ConfigurationWindow(ui.config, ui.events, allow_staging, channel_labels)
    ui.ChannelPage, ui.GeneralPage, ui.EventPage, ui.WaveletPage, ui.SpectrogramPage, ui.PeriodogramPage = ui.ConfigurationWindow.return_page()
    ui.ChannelPage.channelsChanged.connect(lambda ui=ui: settings_changed(ui))
    ui.ChannelPage.channelRenamed.connect(lambda old, new, ui=ui: _rename_channel(ui, old, new))
    ui.ChannelPage.channelAdded.connect(lambda a, b, ui=ui: _add_channel(ui, a, b))
    ui.ChannelPage.channelDeleted.connect(lambda idx, ui=ui: _delete_channel(ui, idx))
    ui.ConfigurationWindow.settingsApplied.connect(
        lambda keys, ui=ui: apply_changes(keys, ui)
    )
    ui.EventPage.changesMade.connect(ui.save_scoring)
    ui.EventPage.eventDeleted.connect(lambda idx, ui=ui: _delete_event(ui, idx))
    # ui.ConfigurationWindow.finished.connect(lambda: save_configuration(ui))
    ui.ConfigurationWindow.show()
