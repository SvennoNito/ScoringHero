from .refresh_gui import refresh_gui

def jump_to_epoch(this_epoch, ui):
    
    ui.this_epoch = this_epoch - 1
    refresh_gui(ui)