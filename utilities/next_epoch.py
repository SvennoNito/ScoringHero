from .refresh_gui import refresh_gui


def next_epoch(ui):
    if ui.this_epoch + 1 < ui.numepo:
        ui.this_epoch += 1
        refresh_gui(ui)
