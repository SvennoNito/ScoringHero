from .refresh_gui import refresh_gui

def first_uncertain_stage(ui):

    for epoch in range(0, ui.numepo):
        if ui.stages[epoch]['uncertain'] == 1:
            ui.this_epoch = epoch
            refresh_gui(ui)
            return   
        


def next_uncertain_stage(ui):

    for epoch in range(ui.this_epoch, ui.numepo):
        if ui.stages[epoch]['uncertain'] == 1:
            ui.this_epoch = epoch
            refresh_gui(ui)
            return   