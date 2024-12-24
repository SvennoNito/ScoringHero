from .refresh_gui import refresh_gui


def first_unscored_epoch(ui):
    for epoch in range(0, ui.numepo):
        if ui.stages[epoch]["stage"] == None:
            ui.this_epoch = epoch
            refresh_gui(ui)
            return


def next_unscored_epoch(ui):
    stages          = [stage["stage"] for stage in ui.stages]
    unscored_epochs = [epoch for epoch, stage in enumerate(stages) if stage is None]
    next_epoch      = min([epoch for epoch in unscored_epochs if epoch > ui.this_epoch], default=None)

    if next_epoch is None:
        next_epoch = min([epoch for epoch in unscored_epochs if epoch <= ui.this_epoch], default=None)

    if next_epoch is not None:
        ui.this_epoch = next_epoch
        refresh_gui(ui)
    return        