"""Scene 0: the window starts empty; load the example recording through File > Load EEG."""

import os

from make_video import assert_empty_start


def run(ctx):
    ctx.caption("ScoringHero starts with no recording loaded")
    ctx.wait(1.5)
    ctx.caption("File > Load EEG > Load EEGLAB structure (.mat)")
    path = os.path.join(ctx.directory, "example_data.mat")
    with ctx.file_dialogs(open=[path]):
        ctx.click_menu("action_load_eeglab")
    ctx.wait_idle()
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    assert getattr(ui, "eeg_data", None) is not None, "the recording did not load"
    assert ui.numepo > 0, "the recording did not load"
    assert_empty_start(ui)
