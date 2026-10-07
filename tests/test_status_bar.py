"""Status bar (epoch, confidence, clock time, file name, scoring state) and the stage badge."""

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
    loaded_ui.config[0].update(Show_stage_badge=True, Stage_badge_position=[0.5, 0.5], Stage_badge_size=24)
    monkeypatch.setattr(loaded_ui, "save_scoring", lambda: None)
    return loaded_ui


def test_status_bar_shows_epoch_confidence_and_clock_time_and_badge_shows_stage(ui):
    _jump(ui, 3)
    text = _status_text(ui)
    assert f"Epoch 4 / {ui.numepo}" in text
    assert "Confidence 85%" in text
    assert "23:01:30" in text  # epoch 4 starts 3 x 30 s after 23:00:00
    assert ui.StatusReadout.stage_badge.text() == "N2"


def test_stage_badge_shows_unscored_not_sure_and_comparison_disagreement(ui):
    _jump(ui, 0)
    assert ui.StatusReadout.stage_badge.text() == "Unscored"
    _jump(ui, 5)
    assert ui.StatusReadout.stage_badge.text() == "REM" and "Not sure" in _status_text(ui)
    ui.scoring_comparison = Scoring(ui.numepo, ui.config[0]["Epoch_length_s"])
    ui.scoring_comparison.set(3, "N3")
    ui.comparison_name = "other"
    _jump(ui, 3)
    text = ui.StatusReadout.stage_badge.text()
    assert "N2" in text and "vs N3" in text
    assert "#c0392b" in text and "font-size" in text and ">vs N3<" in text
    ui.scoring_comparison.set(3, "N2")
    _jump(ui, 3)
    text = ui.StatusReadout.stage_badge.text()
    assert "vs N2" in text and "#c0392b" not in text


def test_status_bar_shows_recording_name_and_comparison(ui):
    _jump(ui, 0)
    assert "EEG: example_data.mat" in _status_text(ui)
    assert "Scoring: example_data.json" in _status_text(ui)
    assert "example_data" not in ui.PaintEventWidget.window().windowTitle()
    assert "Comparison" not in _status_text(ui)
    ui.scoring_comparison = Scoring(ui.numepo, ui.config[0]["Epoch_length_s"])
    ui.scoring_comparison.set(3, "N3")
    ui.comparison_name = "scorer2"
    ui.comparison_suffix = ".annot"
    _jump(ui, 3)
    text = _status_text(ui)
    assert "Comparison: scorer2.annot" in text
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


def test_recording_start_time_is_editable_in_any_time_unit_and_moves_the_status_clock(ui):
    from PySide6.QtCore import QTime

    from config.apply_changes import _finish_changes
    from widgets.configurationWindow import GeneralConfiguration

    ui.config[0]["EEG_panel_time_unit"] = "Seconds"
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    assert page.start_time_edit.isEnabled()
    page.start_time_edit.setTime(QTime(22, 0))
    assert ui.config[0]["Recording_start_time"] == "22:00"
    _finish_changes(["Recording_start_time"], ui)
    assert "22:00:00" in _status_text(ui)


def test_status_bar_also_shows_the_stage(ui):
    _jump(ui, 3)
    assert ui.StatusReadout.stage.text() == "N2"


def test_stage_badge_can_be_hidden_by_config(ui):
    from config.apply_changes import _finish_changes

    badge = ui.StatusReadout.stage_badge
    ui.config[0]["Show_stage_badge"] = False
    _finish_changes(["Show_stage_badge"], ui)
    assert badge.isHidden()
    ui.config[0]["Show_stage_badge"] = True
    _finish_changes(["Show_stage_badge"], ui)
    assert not badge.isHidden()


def test_dragging_the_stage_badge_moves_it_and_saves_its_position(ui, monkeypatch):
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QApplication

    saved = []
    monkeypatch.setattr("ui.setup_ui.save_configuration", lambda u: saved.append(list(u.config[0]["Stage_badge_position"])))
    window = ui.PaintEventWidget.window()
    window.resize(1500, 900)
    window.show()
    assert QTest.qWaitForWindowExposed(window)
    _jump(ui, 3)
    QApplication.processEvents()
    badge = ui.StatusReadout.stage_badge
    before = badge.geometry().center()
    # the widget under the cursor must be the badge, not the rectangle-painting overlay
    assert QApplication.widgetAt(badge.mapToGlobal(badge.rect().center())) is badge
    QTest.mousePress(badge, Qt.LeftButton, pos=QPoint(5, 5))
    QTest.mouseMove(badge, QPoint(-95, 45))
    QTest.mouseRelease(badge, Qt.LeftButton, pos=QPoint(-95, 45))
    after = badge.geometry().center()
    assert (after.x() < before.x()) and (after.y() > before.y())
    fx, fy = ui.config[0]["Stage_badge_position"]
    assert fx < 0.5 and fy > 0.5 and 0 <= fx <= 1 and 0 <= fy <= 1
    assert saved == [[fx, fy]]
    _jump(ui, 4)  # position survives epoch changes
    assert badge.geometry().center() == after
    window.hide()


def test_stage_badge_size_follows_the_config_page(ui):
    from config.apply_changes import _finish_changes
    from widgets.configurationWindow import GeneralConfiguration

    badge = ui.StatusReadout.stage_badge
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    small = badge.height()
    page.spinboxes["Stage_badge_size"][0].setValue(60)
    assert ui.config[0]["Stage_badge_size"] == 60
    _finish_changes(["Stage_badge_size"], ui)
    assert badge.height() > small


def test_stage_badge_size_box_is_disabled_while_the_badge_is_hidden(ui):
    from widgets.configurationWindow import GeneralConfiguration

    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    size_box = page.spinboxes["Stage_badge_size"][0]
    assert size_box.isEnabled()
    page.checkboxes["Show_stage_badge"].setChecked(False)
    assert not size_box.isEnabled()
    page.checkboxes["Show_stage_badge"].setChecked(True)
    assert size_box.isEnabled()


def test_swa_slider_and_periodogram_info_icon_have_tooltips(ui):
    assert "SWA" in ui.HypnogramSlider.slider.toolTip()
    info = ui.RectanglePower.info
    assert "Periodogram" in info.toolTip()
    ui.RectanglePower.axes.resize(300, 300)
    assert info.x() + info.width() <= 300 and info.y() < 20
