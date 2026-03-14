from .refresh_gui import refresh_gui


def first_unscored_epoch(ui):
    for epoch in range(0, ui.numepo):
        if ui.stages[epoch]["stage"] == None:
            ui.this_epoch = epoch
            refresh_gui(ui)
            return


def next_unscored_epoch(ui):
    target = next(
        (e for e in range(ui.this_epoch + 1, ui.numepo) if ui.stages[e]["stage"] is None),
        None
    )
    if target is None:
        target = next(
            (e for e in range(0, ui.this_epoch + 1) if ui.stages[e]["stage"] is None),
            None
        )
    if target is not None:
        ui.this_epoch = target
        refresh_gui(ui)