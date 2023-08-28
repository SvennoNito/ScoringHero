from .refresh_gui import refresh_gui

def first_unscored_epoch(ui):
    
    for epoch in range(0, ui.numepo):
        if ui.stages[epoch]['stage'] == None:
            ui.this_epoch = epoch
            refresh_gui(ui)
            return



def next_unscored_epoch(ui):

    for epoch in range(ui.this_epoch, ui.numepo):
        if ui.stages[epoch]['stage'] == None:
            ui.this_epoch = epoch
            refresh_gui(ui)
            return