"""Scene 1: the window starts empty; load the example recording through File > Load EEG."""

from make_video import assert_empty_start
from utilities.redraw_gui import redraw_gui

LINE_WIDTH = 1.0  # px; the app default is 1.5, too heavy at 1080p


def run(ctx):
    ctx.caption("ScoringHero starts with no recording loaded")
    ctx.wait(1.5)
    ctx.caption("File > Load EEG > Load EEGLAB structure (.mat)")
    with ctx.file_dialogs(open=(ctx.directory, "example_data.mat", "*.mat")):
        ctx.click_menu("action_load_eeglab")
    ctx.wait_idle()
    for channel in ctx.ui.config[1]:
        channel["Line_width"] = LINE_WIDTH
    redraw_gui(ctx.ui)
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    assert getattr(ui, "eeg_data", None) is not None, "the recording did not load"
    assert ui.numepo > 0, "the recording did not load"
    assert_empty_start(ui)
    assert all(c["Line_width"] == LINE_WIDTH for c in ui.config[1]), "channel line width was not applied"
