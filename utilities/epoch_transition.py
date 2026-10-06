from .navigate import jump_to


def stage_transition(ui):
    jump_to(ui, ui.scoring.next_transition(ui.this_epoch))
