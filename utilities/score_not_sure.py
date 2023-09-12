def score_not_sure(ui):
    # Change uncertainty
    ui.stages[ui.this_epoch]["uncertain"] = change_value(ui.stages[ui.this_epoch]["uncertain"])

    # Update text
    # ui.DisplayedEpochWidget.change_uncertainty(ui.stages[ui.this_epoch]["uncertain"])
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)

    # Update hypnpgram
    # ui.HypnogramWidget.draw_hypnogram(ui.stages, ui.numepo, ui.config, ui.swa)


def change_value(value):
    if value == 1:
        return 0
    else:
        return 1
