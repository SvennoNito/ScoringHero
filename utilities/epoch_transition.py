from .refresh_gui import refresh_gui


def stage_transition(ui):
    this_stage = ui.stages[ui.this_epoch]["stage"]

    # Find epochs where the stage is different
    transition_epochs = [
        epoch for epoch, stage in enumerate(ui.stages)
        if stage["stage"] != this_stage
    ]

    # Find the closest larger epoch with a stage change
    next_epoch = min([epoch for epoch in transition_epochs if epoch > ui.this_epoch], default=None)

    # Fallback: if no larger epoch is found, search earlier epochs
    if next_epoch is None:
        next_epoch = min([epoch for epoch in transition_epochs if epoch <= ui.this_epoch], default=None)

    # Update and refresh GUI if a transition epoch is found
    if next_epoch is not None:
        ui.this_epoch = next_epoch
        refresh_gui(ui)
    return

