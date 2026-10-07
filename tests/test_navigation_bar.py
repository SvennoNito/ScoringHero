"""Navigation bar: icon-only jump buttons on the left, observed through the booted app."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolBar

from scoring_model.events import N_SLOTS
from scoring_model.scoring import HUMAN, Scoring

NAMES = [
    "Next unscored", "Next uncertain", "Next stage transition",
    "Next event", "Next human-scored", "Next disagreement",
]


def _button(ui, name):
    return next(a for a in ui.navigation_bar.actions() if a.text() == name)


def test_navigation_bar_is_the_only_bar_and_sits_vertically_on_the_left(loaded_ui):
    bar = loaded_ui.navigation_bar
    window = bar.parentWidget()
    assert window.findChildren(QToolBar) == [bar]
    assert window.toolBarArea(bar) == Qt.LeftToolBarArea
    assert bar.orientation() == Qt.Vertical
    assert bar.toolButtonStyle() == Qt.ToolButtonIconOnly
    assert [a.text() for a in bar.actions()] == NAMES
    assert all(not a.icon().isNull() for a in bar.actions())


def test_buttons_wait_for_a_recording_and_disagreement_for_a_comparison(unloaded_ui, loaded_ui):
    assert all(not _button(unloaded_ui, n).isEnabled() for n in NAMES)
    for name in NAMES[:-1]:
        assert _button(loaded_ui, name).isEnabled(), name
    assert not _button(loaded_ui, "Next disagreement").isEnabled()

    loaded_ui.scoring_comparison = Scoring(loaded_ui.numepo, loaded_ui.config[0]["Epoch_length_s"])
    loaded_ui.tool_nextdisagreement.setEnabled(True)  # what importing a comparison does
    assert _button(loaded_ui, "Next disagreement").isEnabled()


def test_tooltips_give_a_sentence_and_rule_and_disabled_buttons_say_why(unloaded_ui, loaded_ui):
    uncertain = _button(loaded_ui, "Next uncertain").toolTip()
    assert "Jump to next <b>uncertain</b> epoch" in uncertain and "confidence is below 0.5" in uncertain

    assert "open a recording first" in _button(unloaded_ui, "Next event").toolTip().lower()
    disagreement = _button(loaded_ui, "Next disagreement")
    assert "load a comparison scoring first" in disagreement.toolTip().lower()

    loaded_ui.tool_nextdisagreement.setEnabled(True)
    assert "comparison scoring first" not in disagreement.toolTip().lower()
    assert "differs" in disagreement.toolTip()


@pytest.fixture
def scored(loaded_ui, monkeypatch):
    ui = loaded_ui
    ui.scoring = Scoring(ui.numepo, ui.config[0]["Epoch_length_s"])
    ui.scoring.set(range(ui.numepo), "N2", "GSSC", 0.9, [])
    ui.scoring.set(2, "N2", "GSSC", 0.1)
    ui.scoring.set(5, "N3", HUMAN)
    ui.scoring.set(9, None)
    ui.scoring_comparison = Scoring(ui.numepo, ui.config[0]["Epoch_length_s"])
    ui.scoring_comparison.set(range(ui.numepo), "N2")
    ui.scoring_comparison.set(5, "N3")
    ui.scoring_comparison.set(7, "REM")
    ui.tool_nextdisagreement.setEnabled(True)
    ui.this_epoch = 0
    monkeypatch.setattr(ui, "save_scoring", lambda: None)
    return ui


@pytest.mark.parametrize("name, expected", [
    ("Next unscored", 9),
    ("Next uncertain", 2),
    ("Next stage transition", 5),
    ("Next human-scored", 5),
    ("Next disagreement", 7),
])
def test_jump_buttons_move_to_the_next_matching_epoch(scored, name, expected):
    _button(scored, name).trigger()
    assert scored.this_epoch == expected


def test_event_jump_button_moves_to_the_next_event_epoch(scored):
    length = scored.config[0]["Epoch_length_s"]
    for slot in range(N_SLOTS):
        scored.edit_events(lambda events, slot=slot: events.clear(slot))
    scored.edit_events(lambda events: events.add(1, [(12 * length + 1, 12 * length + 3)]))
    _button(scored, "Next event").trigger()
    assert scored.this_epoch == 12
