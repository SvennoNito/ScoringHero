def refresh_gui(ui):

    # Update EEG signal
    ui.SignalWidget.update_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)