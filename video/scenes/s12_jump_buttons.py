"""Scene 12: press every Jump button on the Navigation bar in turn. Needs no Comparison scoring.

Hover vs click is decided at film time: a button that is disabled or has no target from the
current Epoch is only hovered, with a caption explaining it would jump to one, and the displayed
Epoch must not change. A button with a target is clicked and the displayed Epoch must move to it.
No Epoch is cleared or staged by hand. "Next uncertain" is the exception: it is always pressed
(a no-op without target) and reported rather than asserted when it has none.
"""

from PySide6.QtWidgets import QToolTip

from scoring_model.scoring import UNCERTAIN_BELOW

TOOLTIP_SECONDS = 1.5  # each Jump button's tooltip stays on screen at least this long


def _next_disagreement(ui):
    if ui.scoring_comparison is None:
        return None
    return ui.scoring.next_disagreement(ui.this_epoch, ui.scoring_comparison)


# ui attribute -> (caption, target epoch from the current epoch)
BUTTONS = [
    ("tool_nextunscored", "Next unscored", lambda ui: ui.scoring.next_unscored(ui.this_epoch)),
    ("tool_nextuncertain", "Next uncertain", lambda ui: ui.scoring.next_uncertain(ui.this_epoch)),
    ("tool_nexttransition", "Next stage transition", lambda ui: ui.scoring.next_transition(ui.this_epoch)),
    ("tool_nextevent", "Next event", lambda ui: ui.events.next_event_epoch(ui.this_epoch)),
    ("tool_nexthuman", "Next human-scored", lambda ui: ui.scoring.next_human(ui.this_epoch)),
    ("tool_nextdisagreement", "Next disagreement", _next_disagreement),
]


def run(ctx):
    ui = ctx.ui
    ctx.state["s12_visited"] = {}  # ui attribute -> {name, hover_only, clicked, before, after}
    ctx.state["s12_uncertain_target"] = ui.scoring.next_uncertain(ui.this_epoch) is not None
    if not ctx.state["s12_uncertain_target"]:
        print("s12: no Epoch with confidence below UNCERTAIN_BELOW "
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
        button = ui.navigation_bar.widgetForAction(action)
        before = ui.this_epoch
        expected = target_of(ui)
        has_target = action.isEnabled() and expected is not None and expected != before
        uncertain = attribute == "tool_nextuncertain" and action.isEnabled()
        hover_only = not has_target and not uncertain
        if not action.isEnabled():
            assert expected is None, f"'{name}' is disabled but has a target (epoch {expected})"
        if hover_only:
            ctx.caption(f"{name}: no such Epoch from here \u2014 would jump to one, hover only")
        else:
            ctx.caption(name)

        ctx.move_cursor(button, duration=1.0)
        # synthetic mouse moves don't start Qt's tooltip timer: show the button's tooltip directly
        QToolTip.showText(ctx.to_global(ctx._cursor.toPoint()), action.toolTip(), button)
        assert QToolTip.isVisible(), f"no tooltip shown for '{name}'"
        ctx.wait(TOOLTIP_SECONDS)
        QToolTip.hideText()

        if hover_only:
            assert ui.this_epoch == before, f"hovering '{name}' moved the displayed Epoch"
            record = {"name": name, "hover_only": True, "clicked": False, "before": before, "after": ui.this_epoch}
        else:
            ctx.click(button, duration=0.1)
            ctx.wait_idle()
            assert pressed and pressed[-1] is action, f"the click did not press '{name}'"
            if has_target:
                assert ui.this_epoch == expected, f"'{name}': went to epoch {ui.this_epoch}, expected {expected}"
            else:
                assert ui.this_epoch == before, f"'{name}': moved to {ui.this_epoch} despite no target"
            record = {"name": name, "hover_only": False, "clicked": True, "before": before, "after": ui.this_epoch}
        ctx.state["s12_visited"][attribute] = record
        if not hover_only:
            ctx.wait(1.5)
    ctx.caption(None)
    print("s12: " + ", ".join(f"{r['name']} -> {None if r['hover_only'] else r['after']}"
                                for r in ctx.state["s12_visited"].values()), flush=True)


def check(ctx):
    visited = ctx.state["s12_visited"]
    assert list(visited) == [attribute for attribute, _, _ in BUTTONS], "not every Jump button was visited in turn"
    for attribute, record in visited.items():
        if record["hover_only"]:
            assert not record["clicked"], f"'{record['name']}' is hover-only but was clicked"
            assert record["after"] == record["before"], f"hovering '{record['name']}' moved the Epoch"
    if not ctx.state["s12_uncertain_target"]:
        print("s12 check: no real uncertain Epoch existed; 'Next uncertain' target assertion skipped.", flush=True)
