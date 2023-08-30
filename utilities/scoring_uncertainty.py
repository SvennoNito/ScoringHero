def scoring_uncertainty(ui):

    # Change uncertainty
    ui.stages[ui.this_epoch]["uncertain"] = change_value(ui.stages[ui.this_epoch]["uncertain"])

    # Update text
    ui.DisplayedEpochWidget.change_uncertainty(ui.stages[ui.this_epoch]["uncertain"])


    # Update hypnpgram
    #ui.HypnogramWidget.draw_hypnogram(ui.stages, ui.numepo, ui.config, ui.swa) 

def change_value(value):
    if value == 1:
        return 0
    else:
        return 1
