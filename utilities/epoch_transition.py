from .refresh_gui import refresh_gui


def stage_transition(ui):
    this_stage = ui.stages[ui.this_epoch]["stage"]

    target = next(
        (e for e in range(ui.this_epoch + 1, ui.numepo) if ui.stages[e]["stage"] != this_stage),
        None
    )
    if target is None:
        target = next(
            (e for e in range(0, ui.this_epoch + 1) if ui.stages[e]["stage"] != this_stage),
            None
        )
    if target is not None:
        ui.this_epoch = target
        refresh_gui(ui)

