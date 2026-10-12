"""Scene 2: score the first ten Epochs Wake by hand, right after the recording loads.

Click each of the first ten Epochs in turn and press the Wake hotkey (W); the app scores
the Epoch and the Hypnogram visibly builds up one Epoch at a time, before any Autoscorer runs.
"""

from PySide6.QtCore import Qt

N_EPOCHS = 10
KEY = Qt.Key_W


def run(ctx):
    ui = ctx.ui
    ctx.wait_idle()
    ctx.window.activateWindow()  # offscreen: shortcuts only fire in the active window
    ctx.app.processEvents()
    ctx.state["s02_before"] = list(ui.scoring.stages()[:N_EPOCHS])

    ctx.caption("Stage the first ten Epochs Wake by hand: click an Epoch, then press W")
    ctx.wait(1.0)
    for epoch in range(N_EPOCHS):
        ctx.click_epoch(epoch)
        ctx.press_key(KEY, seconds=0.6)
        print(f"s02: epoch {epoch} -> Wake", flush=True)
    ctx.wait(1.0)
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    before = ctx.state["s02_before"]
    assert all(stage is None for stage in before), "the first ten Epochs were already staged before this scene ran"
    stages = ui.scoring.stages()
    staged = [i for i, stage in enumerate(stages) if stage is not None]
    assert staged == list(range(N_EPOCHS)), f"expected exactly Epochs 0-{N_EPOCHS - 1} staged, got {staged}"
    assert all(stages[i] == "Wake" for i in range(N_EPOCHS)), f"not all of the first {N_EPOCHS} Epochs are Wake: {stages[:N_EPOCHS]}"
