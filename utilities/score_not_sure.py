from scoring.write_scoring import write_scoring

def score_not_sure(ui):
    # Change uncertainty
    ui.stages[ui.this_epoch]["confidence"] = change_value(ui.stages[ui.this_epoch]["confidence"])
    ui.stages[ui.this_epoch]["source"] = "human"

    # Update text
    # ui.DisplayedEpochWidget.change_uncertainty(ui.stages[ui.this_epoch]["uncertain"])
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)

    # Update hypnpgram
    # ui.HypnogramWidget.draw_hypnogram(ui.stages, ui.numepo, ui.config, ui.swa)

    write_scoring(ui)


def change_value(value):
    if value != 0:
        return 0
    else:
        return None
