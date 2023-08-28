from utilities import *

def click_on_hypnogram(event, ui):
    ui.this_epoch = ui.HypnogramWidget.coordinates_upon_mousclick(event, ui.config[0]['Epoch_length_s'])
    refresh_gui(ui)