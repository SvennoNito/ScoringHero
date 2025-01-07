from .refresh_gui import refresh_gui


def first_uncertain_stage(ui):
    for epoch in range(0, ui.numepo):
        if ui.stages[epoch]["confidence"] != None:
            if ui.stages[epoch]["confidence"] < .5:
                ui.this_epoch = epoch
                refresh_gui(ui)
                return


def next_uncertain_stage(ui):
    uncertain_epochs = [
        epoch for epoch, stage in enumerate(ui.stages)
        if stage["confidence"] is not None and stage["confidence"] < 0.5
    ]
    next_epoch = min([epoch for epoch in uncertain_epochs if epoch > ui.this_epoch], default=None)

    if next_epoch is None:
        next_epoch = min([epoch for epoch in uncertain_epochs if epoch <= ui.this_epoch], default=None)

    if next_epoch is not None:
        ui.this_epoch = next_epoch
        refresh_gui(ui)
    return

