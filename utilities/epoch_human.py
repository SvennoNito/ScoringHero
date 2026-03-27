from .refresh_gui import refresh_gui


def next_human_epoch(ui):
    target = next(
        (e for e in range(ui.this_epoch + 1, ui.numepo) if ui.stages[e]["source"] == "human"),
        None
    )
    if target is None:
        target = next(
            (e for e in range(0, ui.this_epoch + 1) if ui.stages[e]["source"] == "human"),
            None
        )
    if target is not None:
        ui.this_epoch = target
        refresh_gui(ui)
