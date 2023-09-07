from utilities.refresh_gui import refresh_gui


def click_on_spectogram(event, ui):
    ui.this_epoch = ui.SpectogramWidget.coordinates_upon_mousclick(event)
    refresh_gui(ui)
