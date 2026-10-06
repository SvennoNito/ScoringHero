from .refresh_gui import refresh_gui


def jump_to(ui, target):
    """Show epoch `target` (a Scoring query result); None means no match: stay."""
    if target is not None:
        ui.this_epoch = target
        refresh_gui(ui)
