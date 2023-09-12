from .refresh_gui import refresh_gui


def stage_transition(ui):
    this_stage = ui.stages[ui.this_epoch]["stage"]
    for epoch in range(ui.this_epoch + 1, ui.numepo):
        if ui.stages[epoch]["stage"] != this_stage:
            ui.this_epoch = epoch
            refresh_gui(ui)
            return
