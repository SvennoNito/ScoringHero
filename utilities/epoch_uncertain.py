from .refresh_gui import refresh_gui


def first_uncertain_stage(ui):
    for epoch in range(0, ui.numepo):
        if ui.stages[epoch]["confidence"] != None:
            if ui.stages[epoch]["confidence"] < .5:
                ui.this_epoch = epoch
                refresh_gui(ui)
                return


def next_uncertain_stage(ui):
    target = next(
        (e for e in range(ui.this_epoch + 1, ui.numepo)
         if ui.stages[e]["confidence"] is not None and ui.stages[e]["confidence"] < 0.5),
        None
    )
    if target is None:
        target = next(
            (e for e in range(0, ui.this_epoch + 1)
             if ui.stages[e]["confidence"] is not None and ui.stages[e]["confidence"] < 0.5),
            None
        )
    if target is not None:
        ui.this_epoch = target
        refresh_gui(ui)

