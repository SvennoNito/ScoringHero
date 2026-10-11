"""Scene 6: press every Jump button on the Navigation bar, in turn, after the spindles exist.

Off camera, a few Epochs are prepared so that every button has a visible target (the autoscored
night has no unscored or human-scored Epochs and no Comparison scoring): a few Epochs unscored,
a few human-scored, one uncertain, and a temporary Comparison scoring that disagrees on a few
Epochs. The Primary scoring and the Comparison scoring are restored at the end.
"""

import copy

from scoring_model.scoring import HUMAN, STAGES, UNCERTAIN_BELOW
from scoring.scoring_import_comparison import clear_comparison
from utilities.refresh_gui import refresh_gui

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


def _prepare(ui):
    """Give every Jump button a target; returns the Primary scoring's state to restore."""
    scoring, n = ui.scoring, ui.numepo
    saved = copy.deepcopy(scoring.__dict__)
    for epoch in (n // 5, n // 2, 4 * n // 5):
        scoring.set(epoch, None)
    for epoch in (n // 3, 2 * n // 3):
        scoring.set(epoch, scoring.stage(epoch) or "N2", source=HUMAN, confidence=1.0)
    if scoring.next_uncertain(0) is None:
        epoch = n // 4
        scoring.set(epoch, scoring.stage(epoch) or "N2", source=scoring.source(epoch),
                    confidence=UNCERTAIN_BELOW / 2)

    comparison = copy.deepcopy(scoring)
    for epoch in (n // 10, 3 * n // 5, 9 * n // 10):
        other = STAGES[(STAGES.index(comparison.stage(epoch) or "N2") + 1) % len(STAGES)]
        comparison.set(epoch, other)
    ui.scoring_comparison = comparison
    ui.comparison_name = "Comparison"
    ui.tool_nextdisagreement.setEnabled(True)
    ui.HypnogramWidget.draw_hypnogram(ui)
    return saved


def _restore(ui, saved):
    ui.scoring.__dict__.update(saved)
    clear_comparison(ui)
    ui.HypnogramWidget.draw_hypnogram(ui)
    refresh_gui(ui)


def run(ctx):
    ui = ctx.ui
    ctx.wait_until(lambda: not getattr(ui, "_busy_runners", None))  # the busy indicator swallows mouse input
    saved = _prepare(ui)
    ctx.state["s06_visited"] = []
    pressed = []
    actions = {attribute: getattr(ui, attribute) for attribute, _, _ in BUTTONS}
    for action in actions.values():
        action.triggered.connect(lambda checked=False, a=action: pressed.append(a))
    try:
        ctx.caption("Navigation bar: one Jump button per kind of Epoch")
        ctx.wait(1.5)
        for attribute, name, target_of in BUTTONS:
            action = actions[attribute]
            assert action.isEnabled(), f"Jump button '{name}' is disabled"
            expected, before = target_of(ui), ui.this_epoch
            assert expected is not None and expected != before, f"'{name}' has no visible target"
            ctx.caption(name)
            ctx.click(ui.navigation_bar.widgetForAction(action), duration=1.0)
            ctx.wait_until(lambda: not getattr(ui, "_busy_runners", None))
            assert pressed and pressed[-1] is action, f"the click did not press '{name}'"
            assert ui.this_epoch == expected, f"'{name}': went to epoch {ui.this_epoch}, expected {expected}"
            ctx.state["s06_visited"].append((name, ui.this_epoch))
            ctx.wait(1.5)
        ctx.caption(None)
    finally:
        _restore(ui, saved)
    ctx.wait(0.5)
    print("s06: " + ", ".join(f"{n} -> {e}" for n, e in ctx.state["s06_visited"]), flush=True)


def check(ctx):
    ui = ctx.ui
    names = [name for _, name, _ in BUTTONS]
    assert [n for n, _ in ctx.state["s06_visited"]] == names, "not every Jump button was pressed in turn"
    assert ui.scoring_comparison is None and not ui.tool_nextdisagreement.isEnabled(), "temporary Comparison scoring left"
    assert not any(s is None for s in ui.scoring.stages()), "prepared unscored Epochs were not restored"
    assert not any(ui.scoring.source(e) == HUMAN for e in range(ui.numepo)), "prepared human-scored Epochs were not restored"
