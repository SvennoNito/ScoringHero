"""Scene 12: import a Comparison scoring through a real, filmed file dialog, show the comparison
summary statistics, then demo every Jump button on the Navigation bar, then remove the
Comparison scoring.

No Epoch is cleared or staged by hand in this scene: after GSSC every Epoch already has a Stage,
so "Next unscored" and "Next human-scored" have no real target. Those two buttons are only
hovered, with a caption explaining what they would do, and the displayed Epoch must not change.
"Next stage transition", "Next event" and "Next disagreement" already have real targets at this
point (the GSSC-staged night, the spindle Events from earlier scenes, and the Comparison scoring
just imported), and are clicked for real. "Next uncertain" has no seeded target: if GSSC produced
no Epoch with confidence below UNCERTAIN_BELOW, that button is still pressed (a no-op) but
reported instead of asserted.
"""

import copy
import os
from unittest import mock

import numpy as np
from PySide6.QtWidgets import QDialog, QToolTip

from scoring import scoring_import_comparison as import_module
from scoring_model.formats import FORMATS, write_scoringhero
from scoring_model.scoring import HUMAN, STAGES, UNCERTAIN_BELOW

CHANGED_FRACTION = 0.15  # share of epochs the second scorer disagrees on
COMPARISON_FILENAME = "example_data_scorer2.json"

HOVER_ONLY = {"tool_nextunscored", "tool_nexthuman"}  # no real target after GSSC: hover, don't click
TOOLTIP_SECONDS = 1.5  # each Jump button's tooltip stays on screen at least this long

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
    path = os.path.join(ctx.directory, COMPARISON_FILENAME)
    write_scoringhero(scoring, path, [])
    ctx.state["s12_changed"] = len(changed)
    return path


def _jump_button_demo(ctx):
    """Press every Navigation-bar Jump button in turn, using the real targets already in place
    (the GSSC-staged Stage transitions, the spindle Events and the Comparison disagreements just
    imported). "Next unscored" and "Next human-scored" have no real target after GSSC: they are
    only hovered, not clicked."""
    ui = ctx.ui
    ctx.state["s12_visited"] = []
    ctx.state["s12_uncertain_target"] = ui.scoring.next_uncertain(ui.this_epoch) is not None
    if not ctx.state["s12_uncertain_target"]:
        print("s12: GSSC gave no Epoch with confidence below UNCERTAIN_BELOW "
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
        button = ui.navigation_bar.widgetForAction(action)
        before = ui.this_epoch
        expected = target_of(ui)
        hover_only = attribute in HOVER_ONLY
        if hover_only:
            assert expected is None, f"'{name}' unexpectedly has a target after GSSC (epoch {expected})"
            ctx.caption(f"{name}: no such Epoch after GSSC \u2014 would jump to one, hover only")
        else:
            has_target = expected is not None and expected != before
            if attribute != "tool_nextuncertain":
                assert has_target, f"'{name}' has no visible target"
            ctx.caption(name)

        ctx.move_cursor(button, duration=1.0)
        # synthetic mouse moves don't start Qt's tooltip timer: show the button's tooltip directly
        QToolTip.showText(ctx.to_global(ctx._cursor.toPoint()), action.toolTip(), button)
        assert QToolTip.isVisible(), f"no tooltip shown for '{name}'"
        ctx.wait(TOOLTIP_SECONDS)
        QToolTip.hideText()

        if hover_only:
            assert ui.this_epoch == before, f"hovering '{name}' moved the displayed Epoch"
            ctx.state["s12_visited"].append((name, None))
        else:
            ctx.click(button, duration=0.1)
            ctx.wait_idle()
            assert pressed and pressed[-1] is action, f"the click did not press '{name}'"
            if has_target:
                assert ui.this_epoch == expected, f"'{name}': went to epoch {ui.this_epoch}, expected {expected}"
            else:
                assert ui.this_epoch == before, f"'{name}': moved to {ui.this_epoch} despite no target"
            ctx.state["s12_visited"].append((name, ui.this_epoch))
            ctx.wait(1.5)
    ctx.caption(None)
    print("s12: " + ", ".join(f"{n} -> {e}" for n, e in ctx.state["s12_visited"]), flush=True)


def run(ctx):
    ui = ctx.ui
    ctx.wait_idle()
    ctx.state["s12_path"] = path = make_comparison_file(ctx)
    ctx.caption("Import a Comparison scoring from a second scorer")
    # the format dialog is modal: answer it with the default format (ScoringHero .json)
    assert list(FORMATS.values())[0].file_filter == "*.json", "default import format is not ScoringHero JSON"
    with ctx.file_dialogs(open=(ctx.directory, COMPARISON_FILENAME, "*.json")), \
            mock.patch.object(import_module._FormatDialog, "exec", lambda self: True):
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
    ctx.state["s12_stats_shown"] = bool(dialogs) and dialogs[0].isVisible()
    ctx.wait(4.0)
    for dialog in dialogs:
        dialog.close()
    ctx.wait(0.8)

    _jump_button_demo(ctx)

    ctx.caption("Remove the Comparison scoring again")
    ctx.click_menu("action_remove_comparison")
    ctx.wait(1.5)
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    assert os.path.exists(ctx.state["s12_path"]), "comparison file was not generated"
    assert ctx.state["s12_changed"] > 0, "no epochs were changed in the comparison scoring"
    assert ctx.state["s12_stats_shown"], "summary statistics were not shown"

    visited = dict(ctx.state["s12_visited"])
    names = [name for _, name, _ in BUTTONS]
    assert list(visited) == names, "not every Jump button was pressed in turn"
    for attribute, name, _ in BUTTONS:
        if attribute in HOVER_ONLY:
            assert visited[name] is None, f"'{name}' was clicked, not just hovered"
    if not ctx.state["s12_uncertain_target"]:
        print("s12 check: no real uncertain Epoch existed; 'Next uncertain' target assertion skipped.", flush=True)

    assert ui.scoring_comparison is None, "Comparison scoring was not removed"
    assert not ui.action_comparison_stats.isEnabled(), "comparison statistics still enabled"
