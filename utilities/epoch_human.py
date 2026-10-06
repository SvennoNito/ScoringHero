from .navigate import jump_to


def next_human_epoch(ui):
    jump_to(ui, ui.scoring.next_human(ui.this_epoch))
