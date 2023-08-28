from paint_event import *
#from signal_processing import *

def refresh_gui(ui):

    # Update EEG signal
    ui.SignalWidget.update_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)

    # Update display text
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)

    # Update epoch indicator lines
    ui.SpectogramWidget.update_epoch_indicator(ui.this_epoch)
    ui.HypnogramWidget.update_epoch_indicator(ui.this_epoch)

    # Remove green rectangles
    ui.PaintEventWidget.reset()

    # Remove rectangle size text
    ui.SignalWidget.text_amplitude.setText('')
    ui.SignalWidget.text_amplitude.setText('')

    ## Show power line of epoch
    #power, freqs = trim_power(ui.power[ui.this_epoch], ui.freqs, ui.config[0]['Area_power_upper_limit_hz'], ui.config[0]['Area_power_lower_limit_hz'])
    #power = min_max_scale(power)    

