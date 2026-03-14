from utilities.refresh_gui import refresh_gui


def click_on_spectogram(event, ui):
    epoch = ui.SpectogramWidget.coordinates_upon_mousclick(event)
    if epoch is not None:
        ui.this_epoch = epoch
        refresh_gui(ui)
