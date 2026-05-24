from .refresh_gui import refresh_gui


def next_disagreement_epoch(ui):
    if not ui.disagreement_epochs:
        return

    target = next(
        (e for e in ui.disagreement_epochs if e > ui.this_epoch),
        None,
    )
    if target is None:
        target = ui.disagreement_epochs[0]

    ui.this_epoch = target
    refresh_gui(ui)
