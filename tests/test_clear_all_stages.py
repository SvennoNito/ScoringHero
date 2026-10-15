"""Stages > Clear all stages unscores every epoch of the primary scoring only, after confirmation."""

import pytest
from PySide6.QtWidgets import QMessageBox

from scoring_model.scoring import Scoring
from utilities import clear_all_stages as module


@pytest.fixture
def scored_ui(loaded_ui):
    ui = loaded_ui
    ui.scoring = Scoring(ui.numepo, ui.config[0]["Epoch_length_s"])
    ui.scoring.set(range(ui.numepo), "N2", "human")
    ui.scoring_comparison = Scoring(ui.numepo, ui.config[0]["Epoch_length_s"])
    ui.scoring_comparison.set(range(ui.numepo), "N3", "human")
    ui.events.add(1, [(0.0, 30.0)])
    return ui


def test_confirmed_clears_stages_only(scored_ui, monkeypatch):
    ui = scored_ui
    monkeypatch.setattr(module.QMessageBox, "question", lambda *a, **k: QMessageBox.Yes)

    ui.action_clear_all_stages.trigger()

    assert all(s is None for s in ui.scoring.stages())
    assert all(ui.scoring.source(i) is None for i in range(ui.numepo))
    assert ui.events.spans(1) == [[0.0, 30.0]]
    assert set(ui.scoring_comparison.stages()) == {"N3"}
    assert not ui.action_export_sleep_report.isEnabled()


def test_declined_keeps_stages(scored_ui, monkeypatch):
    ui = scored_ui
    monkeypatch.setattr(module.QMessageBox, "question", lambda *a, **k: QMessageBox.No)

    ui.action_clear_all_stages.trigger()

    assert set(ui.scoring.stages()) == {"N2"}
