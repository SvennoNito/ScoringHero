"""Scene 8: change several Stages by hand with hotkeys.

Click an Epoch in the spectrogram Panel, press a Stage hotkey (W, 1, 2, 3, R); the app scores
the Epoch and advances. Epochs are spread over the night; each gets a hotkey that differs from
its current Stage, so every press visibly changes the Hypnogram.
"""

from PySide6.QtCore import Qt

KEYS = [(Qt.Key_W, "Wake"), (Qt.Key_1, "N1"), (Qt.Key_2, "N2"), (Qt.Key_3, "N3"), (Qt.Key_R, "REM")]
FRACTIONS = [0.15, 0.3, 0.45, 0.6, 0.75, 0.9]


def run(ctx):
    ui = ctx.ui
    ctx.wait_until(lambda: not getattr(ui, "_busy_runners", None))  # the busy indicator swallows mouse input
    ctx.window.activateWindow()  # offscreen: shortcuts only fire in the active window
    ctx.app.processEvents()
    ctx.state["s08_changes"] = changes = []

    ctx.caption("Stages: click an Epoch, then press a hotkey (W, 1, 2, 3, R)")
    ctx.wait(1.0)
    for i, fraction in enumerate(FRACTIONS):
        epoch = min(int(ui.numepo * fraction), ui.numepo - 2)
        ctx.click(ctx.spectrogram_point(epoch), duration=0.9)
        assert ui.this_epoch == epoch, f"click did not jump to epoch {epoch}"
        before = ui.scoring.stages()[epoch]
        key, stage = next(k for k in KEYS[i % len(KEYS):] + KEYS if k[1] != before)
        ctx.caption(f"Epoch {epoch + 1}: {before} \u2192 {stage}")
        ctx.press_key(key, seconds=1.5)
        changes.append((epoch, before, stage))
        print(f"s08: epoch {epoch} {before} -> {stage}", flush=True)
    ctx.wait(1.5)


def check(ctx):
    ui = ctx.ui
    changes = ctx.state["s08_changes"]
    assert len(changes) == len(FRACTIONS), "not all Stage changes were made"
    for epoch, before, stage in changes:
        assert ui.scoring.stages()[epoch] == stage, f"epoch {epoch} is {ui.scoring.stages()[epoch]}, expected {stage}"
        assert before != stage
