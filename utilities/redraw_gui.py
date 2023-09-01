def redraw_gui(ui):

    # Redraw EEG data
    ui.SignalWidget.draw_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)
