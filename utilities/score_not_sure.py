from scoring_model.scoring import HUMAN
from scoring.write_scoring import write_scoring


def score_not_sure(ui):
    # Toggle uncertainty: confidence 0 <-> none. Keeps the epoch's stage and channels.
    epoch = ui.this_epoch
    stage = ui.scoring.stage(epoch)
    if stage is None:
        return  # an unscored epoch carries no confidence or source
    ui.scoring.set(epoch, stage, HUMAN, change_value(ui.scoring.confidence(epoch)),
                   ui.scoring.channels(epoch), ui.scoring.probabilities(epoch))

    ui.DisplayedEpochWidget.update_text(
        ui.this_epoch, ui.numepo, ui.scoring, ui.scoring_comparison, ui.comparison_name
    )

    write_scoring(ui)


def change_value(value):
    if value != 0:
        return 0
    else:
        return None
