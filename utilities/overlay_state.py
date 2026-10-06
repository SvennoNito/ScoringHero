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
