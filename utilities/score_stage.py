from scoring_model.scoring import HUMAN
from .refresh_gui import refresh_gui
from scoring.write_scoring import write_scoring


def score_stage(value, ui):
    channels = [config["Channel_name"] for config in ui.config[1] if config["Display_on_screen"] == 1]
    ui.scoring.set(ui.this_epoch, value, HUMAN if value is not None else None, None, channels)

    # Update hypnogram
    ui.HypnogramWidget.update_hypnogram(ui)

    write_scoring(ui)
    # Advance unless on the last epoch, but always refresh
    ui.this_epoch = min(ui.this_epoch + 1, ui.numepo - 1)
    refresh_gui(ui)
