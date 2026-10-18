"""Scene 6: run the GSSC Autoscorer for stages, chosen from the Autoscorer menu.

GSSC needs its optional dependency: run with `uv run --extra gssc python video/make_video.py ...`.
The real GSSC run happens off camera; a short "processing" card replaces the wait.

Epochs 0-9 are already staged Wake by s02_manual_stages before this scene runs, so clicking
OK triggers the real "existing scores detected" QMessageBox from ask_staging_options
(autoscoring/staging_dialogs.py); its QMessageBox.exec is scope-patched to click the real
"Overwrite all" button so GSSC overwrites the whole night.
"""

from unittest import mock

from PySide6.QtWidgets import QMessageBox, QScrollArea

EEG_CHANNELS = ["F3-A2", "F4-A1"]
EOG_CHANNELS = ["EOG1", "EOG2"]


def _tick(ctx, checkboxes, names):
    """Click the checkbox of each channel in `names`, scrolling its list into view first."""
    for name in names:
        box = next((b for b in checkboxes if b.text() == name), None)
        if box is None:
            raise LookupError(f"GSSC window has no channel '{name}'")
        scroll = next(s for s in ctx.ui.GsscWindow.findChildren(QScrollArea) if s.isAncestorOf(box))
        scroll.ensureWidgetVisible(box)
        ctx.app.processEvents()
        ctx.click(ctx.at(box, min(0.5, box.sizeHint().width() / 2) / box.width(), 0.5), duration=0.6)  # a checkbox only reacts on its indicator and text: aim at the middle of those
        assert box.isChecked(), f"clicking GSSC channel '{name}' did not tick it"


def _click_overwrite_all(ctx):
    """Replaces QMessageBox.exec for the "existing scores detected" dialog: clicks the real
    "Overwrite all" button so Qt's own clickedButton() bookkeeping fires correctly."""

    def exec_and_click(msg):
        button = next((b for b in msg.buttons() if b.text() == "Overwrite all"), None)
        if button is None:
            raise LookupError("GSSC's existing-scores dialog has no 'Overwrite all' button")
        button.click()
        ctx.state["s06_overwrite_clicked"] = True
        return QMessageBox.Accepted

    return mock.patch.object(QMessageBox, "exec", exec_and_click)


def run(ctx):
    ui = ctx.ui
    try:
        import gssc  # noqa: F401
    except ImportError as error:
        raise RuntimeError("GSSC is not installed: run with `uv run --extra gssc python video/make_video.py`") from error
    ctx.wait_idle()  # earlier scenes' background work blocks mouse input
    ctx.state["s06_stages_before"] = sum(stage is not None for stage in ui.scoring.stages())
    ctx.state["s06_overwrite_clicked"] = False

    ctx.caption("Autoscorer: let GSSC score the Stages of the whole night")
    ctx.click_menu("action_gssc")
    window = ctx.ref("GsscWindow")
    ctx.wait(0.5)
    ctx.caption("Pick the EEG and EOG channels")
    _tick(ctx, window._eeg_checkboxes, EEG_CHANNELS)
    _tick(ctx, window._eog_checkboxes, EOG_CHANNELS)
    ctx.wait(0.5)

    with _click_overwrite_all(ctx):
        ctx.click(ctx.button(window, "OK"), duration=0.8)  # GSSC starts on the next event-loop turn
    ctx.caption("GSSC is scoring the night…")
    ctx.processing_card("Processing…", 2.0, until=lambda: _scored(ui) and not ctx.progress_dialogs())
    ctx.caption("The Hypnogram is filled with the GSSC Stages")
    ctx.move_cursor(ctx.center(ui.HypnogramWidget), duration=1.0)
    ctx.wait(2.0)
    ctx.move_cursor(ctx.center(ui.StatusReadout.confidence))
    ctx.caption("The Autoscorer's Confidence is shown for each Epoch")
    ctx.wait(2.0)
    ctx.caption(None)


def _scored(ui):
    return sum(stage is not None for stage in ui.scoring.stages()) > 0


def check(ctx):
    ui = ctx.ui
    assert ctx.state["s06_stages_before"] == 10, "expected the ten Wake Epochs from manual staging before GSSC ran"
    assert ctx.state["s06_overwrite_clicked"], "GSSC's 'Overwrite all' button was not clicked"
    stages = [stage for stage in ui.scoring.stages() if stage is not None]
    assert len(stages) == ui.numepo, f"GSSC scored {len(stages)} of {ui.numepo} Epochs"
    assert len(set(stages)) >= 3, f"GSSC produced only {sorted(set(stages))}"
    sources = [ui.scoring.source(i) for i in range(10)]
    assert all(source == "GSSC" for source in sources), f"'Overwrite all' did not overwrite the manually-staged Epochs: sources {sources}"
