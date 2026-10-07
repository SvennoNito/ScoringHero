"""Status bar: epoch, stage, confidence, clock time, file name and scoring state."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel

from scoring_model.scoring import HUMAN, Scoring
from utilities.jump_to_epoch import jump_to_epoch


def _status_text(ui):
    return " | ".join(label.text() for label in ui.statusbar.findChildren(QLabel))


def _jump(ui, epoch):
    jump_to_epoch(epoch + 1, ui)


@pytest.fixture
def ui(loaded_ui, monkeypatch):
    n, length = loaded_ui.numepo, loaded_ui.config[0]["Epoch_length_s"]
    loaded_ui.scoring = Scoring(n, length)
    loaded_ui.scoring.set(3, "N2", "GSSC", 0.85, [])
    loaded_ui.scoring.set(4, "N3", HUMAN)
    loaded_ui.scoring.set(5, "REM", HUMAN, 0)
    loaded_ui.config[0]["Recording_start_time"] = "23:00"
    monkeypatch.setattr(loaded_ui, "save_scoring", lambda: None)
    return loaded_ui


def test_status_bar_shows_epoch_stage_confidence_and_clock_time(ui):
    _jump(ui, 3)
    text = _status_text(ui)
    assert f"Epoch 4 / {ui.numepo}" in text
    assert "N2" in text
    assert "Confidence 85%" in text
    assert "23:01:30" in text  # epoch 4 starts 3 x 30 s after 23:00:00


def test_status_bar_shows_unscored_epochs_and_not_sure_epochs(ui):
    _jump(ui, 0)
    assert "Unscored" in _status_text(ui)
    _jump(ui, 5)
    assert "REM" in _status_text(ui) and "Not sure" in _status_text(ui)


def test_status_bar_shows_recording_name_and_comparison(ui):
    _jump(ui, 0)
    assert "example_data" in _status_text(ui)
    assert "Comparison" not in _status_text(ui)
    ui.scoring_comparison = Scoring(ui.numepo, ui.config[0]["Epoch_length_s"])
    ui.scoring_comparison.set(3, "N3")
    ui.comparison_name = "scorer2"
    _jump(ui, 3)
    text = _status_text(ui)
    assert "Comparison: scorer2" in text
    assert "scorer2: N3" in text


def test_nothing_is_drawn_over_the_signal(ui):
    _jump(ui, 3)
    texts = [label.text() for label in ui.SignalWidget.axes.findChildren(QLabel)]
    assert not any("Epoch" in text for text in texts)


def _enter_epoch_number(ui, digits):
    QTest.mouseClick(ui.EpochReadout.label, Qt.LeftButton)
    ui.EpochReadout.spin.lineEdit().selectAll()
    QTest.keyClicks(ui.EpochReadout.spin.lineEdit(), digits)
    QTest.keyClick(ui.EpochReadout.spin, Qt.Key_Return)


def test_clicking_the_epoch_readout_lets_you_type_an_epoch_number_to_jump(ui):
    _enter_epoch_number(ui, "12")
    assert ui.this_epoch == 11
    assert ui.EpochReadout.currentWidget() is ui.EpochReadout.label
    assert f"Epoch 12 / {ui.numepo}" in _status_text(ui)


def test_epoch_number_beyond_the_recording_is_clamped(ui):
    ui.EpochReadout.spin.setValue(10**6)
    ui.EpochReadout.spin.editingFinished.emit()
    assert ui.this_epoch == ui.numepo - 1


def test_failed_save_shows_unsaved_changes(ui, monkeypatch):
    import scoringhero

    monkeypatch.setattr(scoringhero, "write_scoring", lambda *args: 1 / 0)
    monkeypatch.setattr(scoringhero.QMessageBox, "critical", lambda *args: None)
    scoringhero.Ui_MainWindow.save_scoring(ui)  # the fixture stubs the instance's save
    assert "Unsaved changes" in _status_text(ui)
