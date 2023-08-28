from .refresh_gui import refresh_gui


def prev_epoch(ui):
    if ui.this_epoch > 0:
        ui.this_epoch -= 1
        refresh_gui(ui)
