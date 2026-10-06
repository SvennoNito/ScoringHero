from .refresh_gui import refresh_gui
from scoring.write_scoring import write_scoring


def score_stage(value, ui):
    stages_notation = {
        "N1": -1,
        "N2": -2,
        "N3": -3,
        # 'N4': -4,
        "Wake": 1,
        "REM": 0,
        "NREM": -1,
        "Inconclusive": 2,
        None: None,
    }

    ui.stages[ui.this_epoch]["stage"] = value
    ui.stages[ui.this_epoch]["digit"] = stages_notation[value]
    ui.stages[ui.this_epoch]["source"] = "human" if value != None else None
    ui.stages[ui.this_epoch]["confidence"] = None
    ui.stages[ui.this_epoch]["channels"] = [config["Channel_name"] for config in ui.config[1] if config["Display_on_screen"] == 1] if value != None else None

    # Update hypnogram
    ui.HypnogramWidget.update_hypnogram(ui)

    write_scoring(ui)
    # Advance unless on the last epoch, but always refresh
    ui.this_epoch = min(ui.this_epoch + 1, ui.numepo - 1)
    refresh_gui(ui)
