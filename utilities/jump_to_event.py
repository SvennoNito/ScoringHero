from itertools import chain
from .refresh_gui import refresh_gui

def jump_to_event(ui):
    event_epochs = []
    for container in ui.AnnotationContainer:
        event_epochs.extend(container.epochs)

    event_epochs     = list(set(chain(*event_epochs)))
    next_epoch = min([epoch for epoch in event_epochs if epoch > ui.this_epoch+1], default=None)

    if next_epoch is None:
        next_epoch = min([epoch for epoch in event_epochs if epoch <= ui.this_epoch+1], default=None)

    if next_epoch is not None:
        ui.this_epoch = next_epoch - 1
        refresh_gui(ui)
    return