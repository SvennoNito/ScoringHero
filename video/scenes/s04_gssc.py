"""Scene 4: run the GSSC Autoscorer for stages, chosen from the Autoscorer menu.

GSSC needs its optional dependency: run with `uv run --extra gssc python video/make_video.py ...`.
The real GSSC run happens off camera; a short "processing" card replaces the wait.
"""

from PySide6.QtWidgets import QScrollArea

EEG_CHANNELS = ["C3-A2", "C4-A1"]
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


def run(ctx):
    ui = ctx.ui
    try:
        import gssc  # noqa: F401
    except ImportError as error:
        raise RuntimeError("GSSC is not installed: run with `uv run --extra gssc python video/make_video.py`") from error
    ctx.wait_idle()  # earlier scenes' background work blocks mouse input
    ctx.state["s04_stages_before"] = sum(stage is not None for stage in ui.scoring.stages())

    ctx.caption("Autoscorer: let GSSC score the Stages of the whole night")
    ctx.click_menu("action_gssc")
    window = ctx.ref("GsscWindow")
    ctx.wait(0.5)
    ctx.caption("Pick the EEG and EOG channels")
    _tick(ctx, window._eeg_checkboxes, EEG_CHANNELS)
    _tick(ctx, window._eog_checkboxes, EOG_CHANNELS)
    ctx.wait(0.5)

    ctx.click(ctx.button(window, "OK"), duration=0.8)  # GSSC starts on the next event-loop turn
    ctx.caption("GSSC is scoring the night…")
    ctx.processing_card("Processing…", 2.0, until=lambda: _scored(ui) and not ctx.progress_dialogs())
    ctx.caption("The Hypnogram is filled with the GSSC Stages")
    ctx.wait(2.5)


def _scored(ui):
    return sum(stage is not None for stage in ui.scoring.stages()) > 0


def check(ctx):
    ui = ctx.ui
    assert ctx.state["s04_stages_before"] == 0, "Primary scoring was not empty before GSSC"
    stages = [stage for stage in ui.scoring.stages() if stage is not None]
    assert len(stages) == ui.numepo, f"GSSC scored {len(stages)} of {ui.numepo} Epochs"
    assert len(set(stages)) >= 3, f"GSSC produced only {sorted(set(stages))}"
