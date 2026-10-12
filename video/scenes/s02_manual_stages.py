"""Scene 2: a short tour of the night via the spectrogram, then score the first ten Epochs
Wake by hand.

Click the spectrogram to jump to four landmark Epochs picked from the example recording's
tracked reference scoring (first N1, first N2, first N3, 10th REM; computed at render time
from the reference file, never loaded into the app, so the numbers track the example data).
Jump back to Epoch 1 via the Epoch counter, then stage it Wake through Stage > Wake and press
the Wake hotkey (W) nine more times; the app auto-advances after each press, so the Hypnogram
visibly builds up one Epoch at a time, before any Autoscorer runs.
"""

import os

from PySide6.QtCore import Qt

from scoring_model.formats import load_scoringhero
from tests.conftest import EXAMPLE_DIR

N_EPOCHS = 10
KEY = Qt.Key_W


def _landmark_epochs():
    """0-based (first N1, first N2, first N3, 10th REM) Epochs from the example recording's
    tracked reference scoring file (read directly, never loaded into the app)."""
    stages = load_scoringhero(os.path.join(EXAMPLE_DIR, "example_data.json")).stages
    rem = [i for i, stage in enumerate(stages) if stage == "REM"]
    return stages.index("N1"), stages.index("N2"), stages.index("N3"), rem[9]


def run(ctx):
    ui = ctx.ui
    ctx.wait_idle()
    ctx.window.activateWindow()  # offscreen: shortcuts only fire in the active window
    ctx.app.processEvents()
    ctx.state["s02_before"] = list(ui.scoring.stages()[:N_EPOCHS])

    n1, n2, n3, tenth_rem = _landmark_epochs()
    ctx.state["s02_landmarks"] = (n1, n2, n3, tenth_rem)
    landmarks = ((n1, "first N1"), (n2, "first N2"), (n3, "first N3"), (tenth_rem, "10th REM"))
    for epoch, label in landmarks:
        ctx.caption(f"Click the spectrogram to jump to the {label} Epoch (Epoch {epoch + 1})")
        ctx.click_epoch(epoch)
        ctx.wait(0.6)

    ctx.caption("Click the Epoch counter and type an Epoch number to jump straight there")
    counter = ctx.ref("EpochCounter")
    ctx.click(counter.label, duration=1.0)
    ctx.wait(0.4)
    ctx.press_key(Qt.Key_1, seconds=0.25)
    ctx.press_key(Qt.Key_Return, seconds=0.2)
    ctx.wait(0.6)

    ctx.caption("Stage Epoch 1 by hand: Stages > Wake")
    ctx.click_menu("action_wake")
    ctx.caption("Press W to stage the rest Wake; the app auto-advances one Epoch at a time")
    for _ in range(N_EPOCHS - 1):
        ctx.press_key(KEY, seconds=0.75)
    ctx.wait(0.5)

    ctx.caption("The Hypnogram builds up as each Epoch is scored")
    ctx.move_cursor(ctx.center(ctx.ref("HypnogramWidget")), duration=1.2)
    ctx.wait(1.5)
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    before = ctx.state["s02_before"]
    assert all(stage is None for stage in before), "the first ten Epochs were already staged before this scene ran"
    stages = ui.scoring.stages()
    staged = [i for i, stage in enumerate(stages) if stage is not None]
    assert staged == list(range(N_EPOCHS)), f"expected exactly Epochs 0-{N_EPOCHS - 1} staged, got {staged}"
    assert all(stages[i] == "Wake" for i in range(N_EPOCHS)), f"not all of the first {N_EPOCHS} Epochs are Wake: {stages[:N_EPOCHS]}"

    expected = _landmark_epochs()
    assert ctx.state["s02_landmarks"] == expected, (
        f"jump targets {ctx.state['s02_landmarks']} did not match the reference scoring's landmark Epochs {expected}"
    )
