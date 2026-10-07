from scoring_model.scoring import HUMAN


def score_not_sure(ui):
    # Toggle uncertainty: confidence 0 <-> none. Keeps the epoch's stage and channels.
    epoch = ui.this_epoch
    stage = ui.scoring.stage(epoch)
    if stage is None:
        return  # an unscored epoch carries no confidence or source
    ui.scoring.set(epoch, stage, HUMAN, change_value(ui.scoring.confidence(epoch)),
                   ui.scoring.channels(epoch), ui.scoring.probabilities(epoch))

    ui.StatusReadout.update(ui)

    ui.save_scoring()


def change_value(value):
    if value != 0:
        return 0
    else:
        return None
