from .next_epoch import next_epoch
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
    # Use cached visible channel indices to get channel names
    if value != None:
        visible_idx = getattr(ui, 'visible_channel_idx', None)
        if visible_idx is None:
            # Fallback to inline filtering if cache not available
            visible_idx = [i for i, ch in enumerate(ui.config[1]) if ch["Display_on_screen"]]
        ui.stages[ui.this_epoch]["channels"] = [ui.config[1][i]["Channel_name"] for i in visible_idx]
    else:
        ui.stages[ui.this_epoch]["channels"] = None

    # Update hypnogram
    ui.HypnogramWidget.update_hypnogram(ui)

    write_scoring(ui)
    next_epoch(ui)
