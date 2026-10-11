"""Scene 10: import a Comparison scoring, show the comparison summary statistics, demo every
Jump button on the Navigation bar, then remove the Comparison scoring.

A few Epochs are cleared and a few are staged by hand, on camera, with real hotkeys, so "Next
unscored" and "Next human-scored" have real targets. "Next stage transition", "Next event" and
"Next disagreement" already have real targets at this point (the GSSC-staged night, the spindle
Events from earlier scenes, and the Comparison scoring just imported). "Next uncertain" has no
seeded target: if GSSC produced no Epoch with confidence below UNCERTAIN_BELOW, that button is
still pressed (a no-op) but reported instead of asserted.
"""

import copy
import os
from unittest import mock

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from scoring import scoring_import_comparison as import_module
from scoring_model.formats import FORMATS, write_scoringhero
from scoring_model.scoring import HUMAN, STAGES, UNCERTAIN_BELOW

CHANGED_FRACTION = 0.15  # share of epochs the second scorer disagrees on

CLEAR_FRACTIONS = [0.2, 0.4, 0.6]  # Epochs cleared by hand -> targets for "Next unscored"
SET_FRACTIONS = [0.3, 0.5, 0.7]  # Epochs staged by hand -> targets for "Next human-scored"
CLEAR_KEY = Qt.Key_Delete  # ui.action_None's shortcut: clears an Epoch's stage
STAGE_KEYS = [(Qt.Key_W, "Wake"), (Qt.Key_1, "N1"), (Qt.Key_2, "N2"), (Qt.Key_3, "N3"), (Qt.Key_R, "REM")]
EVENT_SLOT = 1  # toggled on an Epoch with a real hotkey -> target for "Next event"
EVENT_HOTKEY = Qt.Key_F1

# ui attribute -> (caption, expected target epoch from the current epoch)
BUTTONS = [
    ("tool_nextunscored", "Next unscored", lambda ui: ui.scoring.next_unscored(ui.this_epoch)),
    ("tool_nextuncertain", "Next uncertain", lambda ui: ui.scoring.next_uncertain(ui.this_epoch)),
    ("tool_nexttransition", "Next stage transition", lambda ui: ui.scoring.next_transition(ui.this_epoch)),
    ("tool_nextevent", "Next event", lambda ui: ui.events.next_event_epoch(ui.this_epoch)),
    ("tool_nexthuman", "Next human-scored", lambda ui: ui.scoring.next_human(ui.this_epoch)),
    ("tool_nextdisagreement", "Next disagreement",
     lambda ui: ui.scoring.next_disagreement(ui.this_epoch, ui.scoring_comparison)),
]


def make_comparison_file(ctx):
    """ScoringHero scoring JSON off camera: the Primary scoring as it is now, with ~15% of the
    epochs given a different stage."""
    scoring = copy.deepcopy(ctx.ui.scoring)
    rng = np.random.default_rng(0)
    n = len(scoring)
    changed = sorted(rng.choice(n, size=round(CHANGED_FRACTION * n), replace=False).tolist())
    for epoch in changed:
        others = [s for s in STAGES if s != scoring.stage(epoch)]
        scoring.set(epoch, others[rng.integers(len(others))], source=HUMAN)
    path = os.path.join(ctx.video_dir, "comparison_scoring.json")
    write_scoringhero(scoring, path, [])
    ctx.state["s10_changed"] = len(changed)
    return path


def _clear_and_set_stages(ctx):
    """Clear a few Epochs' stage and set a few others by hand, on camera, with real hotkeys."""
    ui = ctx.ui
    ctx.window.activateWindow()  # offscreen: shortcuts only fire in the active window
    ctx.app.processEvents()

    ctx.caption("Clear a few Epochs' Stage by hand (Delete)")
    ctx.wait(1.0)
    cleared = []
    for fraction in CLEAR_FRACTIONS:
        epoch = round(fraction * ui.numepo)
        ctx.click_epoch(epoch)
        ctx.press_key(CLEAR_KEY, seconds=0.6)
        assert ui.scoring.stage(epoch) is None, f"Epoch {epoch} was not cleared"
        cleared.append(epoch)
    ctx.state["s10_cleared_epochs"] = cleared

    ctx.caption("Stage a few Epochs by hand (W, 1, 2, 3, R)")
    ctx.wait(1.0)
    staged = []
    for i, fraction in enumerate(SET_FRACTIONS):
        epoch = round(fraction * ui.numepo)
        current = ui.scoring.stage(epoch)
        key, stage = next((k, s) for k, s in STAGE_KEYS[i % len(STAGE_KEYS):] + STAGE_KEYS[:i % len(STAGE_KEYS)]
                           if s != current)
        ctx.click_epoch(epoch)
        ctx.press_key(key, seconds=0.6)
        assert ui.scoring.stage(epoch) == stage, f"Epoch {epoch}: expected Stage {stage}, got {ui.scoring.stage(epoch)}"
        assert ui.scoring.source(epoch) == HUMAN, f"Epoch {epoch} was not recorded as human-scored"
        staged.append((epoch, stage))
    ctx.state["s10_staged_epochs"] = staged
    ctx.wait(0.5)


def _install_key_filter(ctx):
    """The Event hotkeys live in the app-wide key filter that scoringhero.main() installs; the
    headless boot has none. Shared with s07 via ctx.state, so running the full film only installs
    one filter."""
    if "key_filter" not in ctx.state:
        import scoringhero as sh

        ctx.state["key_filter"] = sh.GlobalKeyFilter(ctx.ui, ctx.app)
        ctx.app.installEventFilter(ctx.state["key_filter"])


def _add_event(ctx):
    """Toggle a whole Epoch on in an Event slot by hand, on camera, so "Next event" has a real
    target even when this scene runs on its own (e.g. a --scenes s00 s04 s10 smoke run)."""
    ui = ctx.ui
    _install_key_filter(ctx)
    covered = ui.events.covered_epochs(EVENT_SLOT)
    epoch = next(e for e in range(round(0.8 * ui.numepo), ui.numepo) if e not in covered)
    before = ui.events.count(EVENT_SLOT)

    ctx.caption("Add an Event by hand (F1)")
    ctx.wait(0.5)
    ctx.click_epoch(epoch)
    ctx.press_key(EVENT_HOTKEY, seconds=0.6)
    assert ui.events.count(EVENT_SLOT) == before + 1, f"Event hotkey did not add an Event at Epoch {epoch}"
    ctx.state["s10_event_epoch"] = epoch
    ctx.wait(0.5)


def _jump_button_demo(ctx):
    """Press every Navigation-bar Jump button in turn, using the real targets created above (plus
    the Stage transitions, spindle Events and Comparison disagreements already in place)."""
    ui = ctx.ui
    ctx.state["s10_visited"] = []
    ctx.state["s10_uncertain_target"] = ui.scoring.next_uncertain(ui.this_epoch) is not None
    if not ctx.state["s10_uncertain_target"]:
        print("s10: GSSC gave no Epoch with confidence below UNCERTAIN_BELOW "
              f"({UNCERTAIN_BELOW}): 'Next uncertain' has no real target, pressed as a no-op.",
              flush=True)

    pressed = []
    actions = {attribute: getattr(ui, attribute) for attribute, _, _ in BUTTONS}
    for action in actions.values():
        action.triggered.connect(lambda checked=False, a=action: pressed.append(a))

    ctx.caption("Navigation bar: one Jump button per kind of Epoch")
    ctx.wait(1.5)
    for attribute, name, target_of in BUTTONS:
        action = actions[attribute]
        assert action.isEnabled(), f"Jump button '{name}' is disabled"
        expected, before = target_of(ui), ui.this_epoch
        has_target = expected is not None and expected != before
        if attribute != "tool_nextuncertain":
            assert has_target, f"'{name}' has no visible target"
        ctx.caption(name)
        ctx.click(ui.navigation_bar.widgetForAction(action), duration=1.0)
        ctx.wait_idle()
        assert pressed and pressed[-1] is action, f"the click did not press '{name}'"
        if has_target:
            assert ui.this_epoch == expected, f"'{name}': went to epoch {ui.this_epoch}, expected {expected}"
        else:
            assert ui.this_epoch == before, f"'{name}': moved to {ui.this_epoch} despite no target"
        ctx.state["s10_visited"].append((name, ui.this_epoch))
        ctx.wait(1.5)
    ctx.caption(None)
    print("s10: " + ", ".join(f"{n} -> {e}" for n, e in ctx.state["s10_visited"]), flush=True)


def run(ctx):
    ui = ctx.ui
    ctx.wait_idle()
    ctx.state["s10_path"] = path = make_comparison_file(ctx)
    ctx.caption("Import a Comparison scoring from a second scorer")
    # the format dialog is modal: answer it with the default format (ScoringHero .json)
    assert list(FORMATS.values())[0].file_filter == "*.json", "default import format is not ScoringHero JSON"
    with ctx.file_dialogs(open=path), mock.patch.object(import_module._FormatDialog, "exec", lambda self: True):
        ctx.click_menu("action_import_comparison")
    ctx.wait_until(lambda: ui.scoring_comparison is not None)
    assert ui.action_comparison_stats.isEnabled(), "Comparison scoring was not imported"
    ctx.wait(2.0)

    ctx.caption("Show the summary statistics: agreement, Cohen's kappa and confusion matrix")
    dialogs = []

    def show_nonmodal(self):
        dialogs.append(self)
        self.show()
        return 0

    with mock.patch.object(QDialog, "exec", show_nonmodal):
        ctx.click_menu("action_comparison_stats")
    ctx.state["s10_stats_shown"] = bool(dialogs) and dialogs[0].isVisible()
    ctx.wait(4.0)
    for dialog in dialogs:
        dialog.close()
    ctx.wait(0.8)

    _clear_and_set_stages(ctx)
    _add_event(ctx)
    _jump_button_demo(ctx)

    ctx.caption("Remove the Comparison scoring again")
    ctx.click_menu("action_remove_comparison")
    ctx.wait(1.5)
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    assert os.path.exists(ctx.state["s10_path"]), "comparison file was not generated"
    assert ctx.state["s10_changed"] > 0, "no epochs were changed in the comparison scoring"
    assert ctx.state["s10_stats_shown"], "summary statistics were not shown"

    assert ctx.state["s10_cleared_epochs"], "no Epochs were cleared by hand"
    assert ctx.state["s10_staged_epochs"], "no Epochs were staged by hand"
    for epoch in ctx.state["s10_cleared_epochs"]:
        assert ui.scoring.stage(epoch) is None, f"cleared Epoch {epoch} ended up staged"
    for epoch, stage in ctx.state["s10_staged_epochs"]:
        assert ui.scoring.stage(epoch) == stage, f"hand-staged Epoch {epoch} lost its Stage"
        assert ui.scoring.source(epoch) == HUMAN, f"hand-staged Epoch {epoch} lost its human source"
    assert ui.events.count(EVENT_SLOT) > 0, "the Event added by hand is missing"

    names = [name for _, name, _ in BUTTONS]
    assert [n for n, _ in ctx.state["s10_visited"]] == names, "not every Jump button was pressed in turn"
    if not ctx.state["s10_uncertain_target"]:
        print("s10 check: no real uncertain Epoch existed; 'Next uncertain' target assertion skipped.", flush=True)

    assert ui.scoring_comparison is None, "Comparison scoring was not removed"
    assert not ui.action_comparison_stats.isEnabled(), "comparison statistics still enabled"
