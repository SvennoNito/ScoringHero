from .navigate import jump_to


def next_unscored_epoch(ui):
    jump_to(ui, ui.scoring.next_unscored(ui.this_epoch))
