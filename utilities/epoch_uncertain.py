from .navigate import jump_to


def next_uncertain_stage(ui):
    jump_to(ui, ui.scoring.next_uncertain(ui.this_epoch))
