from itertools import chain
from .refresh_gui import refresh_gui

def jump_to_event(ui):
    epochs = []
    for container in ui.AnnotationContainer:
        epochs.extend(container.epochs)
    epochs = list(set(chain(*epochs)))
    next_epochs = [epoch > ui.this_epoch+1 for epoch in epochs]

    if any(next_epochs):
        ui.this_epoch = epochs[[epoch > ui.this_epoch+1 for epoch in epochs].index(True)] - 1
        refresh_gui(ui)
    return