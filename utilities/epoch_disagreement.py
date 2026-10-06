from .navigate import jump_to


def next_disagreement_epoch(ui):
    jump_to(ui, ui.scoring.next_disagreement(ui.this_epoch, ui.scoring_comparison))
