import numpy as np
from widgets import ConfigurationWindow
from utilities.redraw_gui import redraw_gui
from scoring.write_scoring import write_scoring
from .apply_changes import apply_changes
from .write_configuration import write_configuration


def _display_only_change(ui):
    """Channel config change that only affects rendering (visibility, color, scale, shift).
    No signal rebuild or spectrogram recomputation needed."""
    redraw_gui(ui)
    write_configuration(f"{ui.filename}.config.json", ui.config)


def _signal_rebuild_change(ui, chan_idx):
    """Channel config change that modifies the signal (reref, flip, label rename).

    Always rebuilds eeg_data_display (filtering + reref + flip).  Only recomputes
    the spectrogram/wavelet if the changed channel is the one currently feeding
    those panels — otherwise the spectrogram data is still valid.
    """
    from eeg.rebuild_display import rebuild_eeg_data_display
    from signal_processing.recompute_derived import recompute_derived

    rebuild_eeg_data_display(ui)

    spec_chan = ui.config[0].get("Channel_for_spectogram", "")
    wav_chan  = ui.config[0].get("Wavelet_channel", "")
    chan_name = ui.config[1][chan_idx]["Channel_name"] if 0 <= chan_idx < len(ui.config[1]) else ""

    if chan_name in (spec_chan, wav_chan):
        recompute_derived(ui)
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)

    redraw_gui(ui)
    write_configuration(f"{ui.filename}.config.json", ui.config)


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


def _add_channel(ui, channel_a_name, channel_b_name):
    """Add a new derived channel (A − B) to eeg_data and config, then refresh."""
    chan_names = [ch["Channel_name"] for ch in ui.config[1]]
    idx_a = chan_names.index(channel_a_name) if channel_a_name in chan_names else 0

    # Append a copy of channel A's raw signal as the new row
    new_signal = ui.eeg_data[idx_a:idx_a + 1].copy()
    ui.eeg_data = np.vstack([ui.eeg_data, new_signal])

    # Build a default config entry for the new channel (re-reference = B)
    new_name = channel_a_name
    new_chan_config = {
        "Channel_name": new_name,
        "Channel_color": "Black",
        "Display_on_screen": 1,
        "Scaling_factor": 100,
        "Vertical_shift": 0,
        "Re_reference": channel_b_name,
        "Flip_polarity": False,
        "Filter_hp_enabled": False,
        "Filter_hp_cutoff": 0.3,
        "Filter_hp_order": 4,
        "Filter_lp_enabled": False,
        "Filter_lp_cutoff": 50.0,
        "Filter_lp_order": 4,
        "Filter_notch_enabled": False,
        "Filter_notch_cutoff": 50.0,
        "Filter_notch_order": 4,
    }
    ui.config[1].append(new_chan_config)

    # Rebuild display data and refresh all widgets
    apply_changes([], ui)

    # Reset filter window so it rebuilds with the new channel list next time
    ui.FilterWindow = None

    # Close the current config window and reopen on the Channels tab
    ui.ConfigurationWindow.close()
    open_config_window(ui)
    ui.ConfigurationWindow.tabs.setCurrentIndex(1)


def _delete_channel(ui, idx):
    """Remove channel at idx from eeg_data and config, then refresh."""
    del_name = ui.config[1][idx]["Channel_name"]

    # Remove the raw data row
    ui.eeg_data = np.delete(ui.eeg_data, idx, axis=0)

    # Remove the config entry
    ui.config[1].pop(idx)

    # Clear any re-reference that pointed to the deleted channel
    for ch in ui.config[1]:
        if ch.get("Re_reference") == del_name:
            ch["Re_reference"] = "None"

    # Update spectrogram/wavelet/periodogram channel selectors if needed
    remaining_names = [c["Channel_name"] for c in ui.config[1]]
    fallback = remaining_names[0] if remaining_names else ""
    for key in ["Channel_for_spectogram", "Periodogram_channel", "Wavelet_channel"]:
        if ui.config[0].get(key) == del_name:
            ui.config[0][key] = fallback

    # Rebuild display data and refresh
    apply_changes([], ui)

    # Reset filter window so it rebuilds with the updated channel list next time
    ui.FilterWindow = None

    # Close the current config window and reopen on the Channels tab
    ui.ConfigurationWindow.close()
    open_config_window(ui)
    ui.ConfigurationWindow.tabs.setCurrentIndex(1)


def open_config_window(ui):
    allow_staging = all([stage["stage"] == None for stage in ui.stages])

    channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
    ui.ConfigurationWindow = ConfigurationWindow(ui.config, ui.AnnotationContainer, allow_staging, channel_labels)
    ui.ChannelPage, ui.GeneralPage, ui.EventPage, ui.WaveletPage, ui.SpectrogramPage, ui.PeriodogramPage = ui.ConfigurationWindow.return_page()
    ui.ChannelPage.channelMoved.connect(lambda f, t, ui=ui: _move_eeg_row(ui, f, t))
    ui.ChannelPage.changesMade.connect(lambda: apply_changes([], ui))
    ui.ChannelPage.displayOnlyChanged.connect(lambda: _display_only_change(ui))
    ui.ChannelPage.signalRebuildNeeded.connect(lambda idx: _signal_rebuild_change(ui, idx))
    ui.ChannelPage.channelAdded.connect(lambda a, b, ui=ui: _add_channel(ui, a, b))
    ui.ChannelPage.channelDeleted.connect(lambda idx, ui=ui: _delete_channel(ui, idx))
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
