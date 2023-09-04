from paint_event import *
from signal_processing.trim_power import trim_power
from signal_processing.min_max_scale import min_max_scale
from annotations.draw_box_in_epoch import draw_box_in_epoch


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
    ui.SignalWidget.text_amplitude.setText("")
    ui.SignalWidget.text_period.setText("")

    # Show power line of epoch
    power, freqs = trim_power(
        ui.power[ui.this_epoch],
        ui.freqs,
        ui.config[0]["Periodogram_limit_hz"][0],
        ui.config[0]["Periodogram_limit_hz"][1],
    )
    power = min_max_scale(power)
    ui.RectanglePower.update_powerline(freqs, power)

    # Draw annotations
    for container in ui.AnnotationContainer:
        draw_box_in_epoch(ui, container)
