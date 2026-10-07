from scoring_model.scoring import HUMAN
from .refresh_gui import refresh_gui


def score_stage(value, ui):
    if value is None:
        ui.scoring.set(ui.this_epoch, None)
    else:
        channels = [config["Channel_name"] for config in ui.config[1] if config["Display_on_screen"] == 1]
        ui.scoring.set(ui.this_epoch, value, HUMAN, None, channels)

    # Update hypnogram
    ui.HypnogramWidget.update_hypnogram(ui)

    ui.save_scoring()
    # Advance unless on the last epoch, but always refresh
    ui.this_epoch = min(ui.this_epoch + 1, ui.numepo - 1)
    refresh_gui(ui)
