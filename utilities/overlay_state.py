def get_overlay_signal_for_display(ui):
    """Return the overlay signal to draw alongside the primary trace, or None
    if there is no overlay loaded or the user has hidden it."""
    if getattr(ui, "show_overlay", False) and getattr(ui, "eeg_data_display_ref", None) is not None:
        return ui.eeg_data_display_ref
    return None


def get_active_analysis_data(ui):
    """Return the (channels x samples) array that should feed the spectrogram,
    wavelet/TF panel, and PSD -- either the primary recording or the overlay
    signal, depending on the user's Compare > EEG > Analyze selection."""
    if getattr(ui, "analysis_source", "original") == "overlay" and getattr(ui, "eeg_data_display_ref", None) is not None:
        return ui.eeg_data_display_ref
    return ui.eeg_data_display


def toggle_show_overlay(ui, checked):
    ui.show_overlay = checked
    from utilities.redraw_gui import redraw_gui
    redraw_gui(ui)


def set_analysis_source(ui, source, checked):
    if not checked:
        # QActionGroup emits toggled(False) for the action being deselected too;
        # only react to the one being selected.
        return
    if getattr(ui, "analysis_source", "original") == source:
        return
    ui.analysis_source = source

    from eeg.displayed_signal import settings_changed
    settings_changed(ui)


def set_checked_silently(action, checked):
    """Check/uncheck action without emitting toggled. Blocked signals also bypass
    QActionGroup exclusivity: uncheck the other group members explicitly."""
    action.blockSignals(True)
    action.setChecked(checked)
    action.blockSignals(False)


def drop_overlay_signal(ui):
    """Forget the loaded overlay signal; its menu entries go back to: nothing to
    remove or show, analysis on the original signal."""
    ui.eeg_data_ref = None
    ui.show_overlay = False
    ui.analysis_source = "original"
    if hasattr(ui, "action_remove_overlay"):
        ui.action_remove_overlay.setEnabled(False)
        set_checked_silently(ui.action_show_overlay, False)
        ui.action_show_overlay.setEnabled(False)
        ui.menu_analyze_source.setEnabled(False)
        set_checked_silently(ui.action_analyze_original, True)
        set_checked_silently(ui.action_analyze_overlay, False)
