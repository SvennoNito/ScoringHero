"""Interactive scoring paths on the Scoring module, driven through the headless app."""

import time
from types import SimpleNamespace

import pytest
from PySide6 import QtWidgets

from scoring.clean_epochs_to_uistages import clean_epochs_to_uiscoring
from scoring_model.scoring import HUMAN, Scoring, disagreements
from utilities.epoch_disagreement import next_disagreement_epoch
from utilities.epoch_human import next_human_epoch
from utilities.epoch_transition import stage_transition
from utilities.epoch_uncertain import next_uncertain_stage
from utilities.epoch_unscored import next_unscored_epoch
from utilities.score_not_sure import score_not_sure
from utilities.score_stage import score_stage


@pytest.fixture
def ui(boot_scoring, loaded_ui, monkeypatch):
    end = time.time() + 60
    while not hasattr(loaded_ui.HypnogramWidget, "times") and time.time() < end:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.01)
    n, length = loaded_ui.numepo, loaded_ui.config[0]["Epoch_length_s"]
    loaded_ui.scoring = Scoring(n, length)
    loaded_ui.scoring_comparison = None
    monkeypatch.setattr("utilities.score_stage.write_scoring", lambda ui: None)
    monkeypatch.setattr("utilities.score_not_sure.write_scoring", lambda ui: None)
    return loaded_ui


def test_score_stage_sets_human_stage_and_displayed_channels_and_advances(ui):
    ui.this_epoch = 3
    score_stage("N2", ui)
    shown = [c["Channel_name"] for c in ui.config[1] if c["Display_on_screen"] == 1]
    assert ui.scoring.stage(3) == "N2"
    assert ui.scoring.source(3) == HUMAN
    assert ui.scoring.confidence(3) is None
    assert ui.scoring.channels(3) == shown
    assert ui.this_epoch == 4


def test_clearing_stage_clears_source_and_channels(ui):
    ui.this_epoch = 0
    score_stage("REM", ui)
    ui.this_epoch = 0
    score_stage(None, ui)
    assert ui.scoring.stage(0) is None
    assert ui.scoring.source(0) is None
    assert ui.scoring.channels(0) == []


def test_not_sure_toggles_confidence_and_keeps_stage(ui):
    ui.this_epoch = 2
    score_stage("N3", ui)
    ui.this_epoch = 2
    score_not_sure(ui)
    assert ui.scoring.confidence(2) == 0
    assert ui.scoring.stage(2) == "N3"
    assert ui.scoring.source(2) == HUMAN
    assert "not sure" in ui.DisplayedEpochWidget.textfield.text()
    score_not_sure(ui)
    assert ui.scoring.confidence(2) is None


def test_jumps_find_next_and_wrap(ui):
    n = ui.numepo
    ui.scoring.set(range(n), "N2", "GSSC", 0.9, [])
    ui.scoring.set(5, "N3", HUMAN)
    ui.scoring.set(2, "N2", "GSSC", 0.1)
    ui.scoring.set(7, None)

    ui.this_epoch = 0
    next_unscored_epoch(ui)
    assert ui.this_epoch == 7
    next_unscored_epoch(ui)  # single match found again from itself
    assert ui.this_epoch == 7

    ui.this_epoch = 3
    next_uncertain_stage(ui)  # wraps to 2
    assert ui.this_epoch == 2

    ui.this_epoch = 6
    next_human_epoch(ui)  # wraps to 5
    assert ui.this_epoch == 5

    ui.this_epoch = 6
    stage_transition(ui)  # epoch 6 is N2; epoch 7 unscored
    assert ui.this_epoch == 7
    ui.this_epoch = 4
    stage_transition(ui)
    assert ui.this_epoch == 5


def test_jump_without_match_stays(ui):
    ui.scoring.set(range(ui.numepo), "N2", "GSSC", 0.9, [])
    ui.this_epoch = 4
    next_unscored_epoch(ui)
    next_uncertain_stage(ui)
    next_human_epoch(ui)
    stage_transition(ui)
    assert ui.this_epoch == 4


def test_disagreement_follows_edits_of_primary(ui):
    n = ui.numepo
    ui.scoring.set(range(n), "N2", "GSSC", None, [])
    ui.scoring_comparison = Scoring(n, ui.scoring.epoch_length_s)
    ui.scoring_comparison.set(range(n), "N2", "x", None, [])
    ui.scoring_comparison.set([3, 8], "REM", "x")
    ui.comparison_name = "other"

    ui.this_epoch = 0
    next_disagreement_epoch(ui)
    assert ui.this_epoch == 3
    ui.this_epoch = 3
    score_stage("REM", ui)  # resolves epoch 3
    assert disagreements(ui.scoring, ui.scoring_comparison) == [8]
    ui.this_epoch = 3
    next_disagreement_epoch(ui)
    assert ui.this_epoch == 8
    next_disagreement_epoch(ui)  # wraps to itself, the only one
    assert ui.this_epoch == 8


def test_hypnogram_overlay_follows_primary_edits(ui):
    n = ui.numepo
    ui.scoring.set(range(n), "N2", "GSSC", None, [])
    ui.scoring_comparison = Scoring(n, ui.scoring.epoch_length_s)
    ui.scoring_comparison.set(range(n), "N2", "x", None, [])
    ui.scoring_comparison.set([3, 8], "REM", "x")
    ui.HypnogramWidget.draw_hypnogram(ui)
    assert len(ui.HypnogramWidget.comparison_items) == 1
    ui.this_epoch = 3
    score_stage("REM", ui)
    score_stage("REM", ui)  # epoch 4 now disagrees nowhere new; overlay keeps epoch 8 only
    item = ui.HypnogramWidget.comparison_items[0]
    ys = item.getData()[1]
    assert [i // 2 for i, y in enumerate(ys) if y == y and y == 0 and i % 2 == 0] == [8]


def test_comparison_stats_reflect_current_primary(ui, monkeypatch):
    n = ui.numepo
    ui.scoring.set(range(n), "N2", "GSSC", None, [])
    ui.scoring_comparison = Scoring(n, ui.scoring.epoch_length_s)
    ui.scoring_comparison.set(range(n), "N2", "x", None, [])
    ui.scoring_comparison.set([3, 8], "REM", "x")
    ui.this_epoch = 3
    score_stage("REM", ui)

    from scoring import comparison_stats_window as mod

    texts = []
    monkeypatch.setattr(mod.QDialog, "exec", lambda self: texts.extend(
        l.text() for l in self.findChildren(mod.QLabel)))
    mod.comparison_stats_window(ui)
    assert any("Disagreements:</b> 1 epochs" in t for t in texts)


def test_artefact_events_mark_epochs_unclean_through_scoring(ui):
    container = SimpleNamespace(key="A", epochs_set=[{2, 3}, {6}])
    clean_epochs_to_uiscoring(ui, container)
    assert [ui.scoring.clean(i) for i in range(8)] == [1, 0, 0, 1, 1, 0, 1, 1]
    container.epochs_set = [{3}]
    clean_epochs_to_uiscoring(ui, container)
    assert [ui.scoring.clean(i) for i in range(4)] == [1, 1, 0, 1]
    clean_epochs_to_uiscoring(ui, SimpleNamespace(key="B", epochs_set=[{1}]))
    assert ui.scoring.clean(0) == 1
