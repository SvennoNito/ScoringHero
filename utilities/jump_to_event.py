from .refresh_gui import refresh_gui


def jump_to_event(ui):
    next_epoch = ui.events.next_event_epoch(ui.this_epoch)
    if next_epoch is not None:
        ui.this_epoch = next_epoch
        refresh_gui(ui)
