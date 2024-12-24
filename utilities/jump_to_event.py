from itertools import chain
from .refresh_gui import refresh_gui

def jump_to_event(ui):
    epochs = []
    for container in ui.AnnotationContainer:
        epochs.extend(container.epochs)
    epochs = list(set(chain(*epochs)))

    next_epoch    = min([epoch for epoch in epochs if epoch > ui.this_epoch+1], default=None)
    if next_epoch is not None:
        ui.this_epoch = next_epoch
        refresh_gui(ui)
    return