from .next_epoch import next_epoch

def score_stage(value, ui):

    stages_notation = {
        'N1': -1,
        'N2': -2,
        'N3': -3,
        'N4': -4,
        'Wake': 1,
        'REM':  0,
        'NREM': -1
    }

    ui.stages[ui.this_epoch]["stage"] = value
    ui.stages[ui.this_epoch]["digit"] = stages_notation[value]

    next_epoch(ui)

