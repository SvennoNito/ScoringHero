"""Configuration window event page on Events: live labels, counts, durations, clear-slot."""

import json

from config.open_config_window import open_config_window


def _open(ui):
    open_config_window(ui)
    return ui.EventPage


def test_label_edit_is_live_and_saved(loaded_ui):
    ui = loaded_ui
    ui.edit_events(lambda e: e.add(2, [(0, 1)]))
    page = _open(ui)
    page.label[2].setText("spindle")
    assert ui.events.label(2) == "spindle"
    with open(f"{ui.filename}.json") as f:
        records = json.load(f)[1]
    assert [r["event"] for r in records if r["digit"] == 2] == ["spindle"]


def test_counts_durations_and_clear(loaded_ui):
    ui = loaded_ui
    ui.edit_events(lambda e: e.add(3, [(0, 2), (40, 41)]))
    page = _open(ui)
    assert page.count_labels[3].text() == "2"
    assert page.dur_labels[3].text() == "3.0 s"
    ui.edit_events(lambda e: e.clear(3))
    page.refresh()
    assert page.count_labels[3].text() == "0"
    assert page.dur_labels[3].text() == "0.0 s"


def test_clear_slot_zero_marks_epochs_clean(loaded_ui):
    ui = loaded_ui
    ui.edit_events(lambda e: e.add(0, [(0, ui.events.epoch_length_s)]))
    assert not ui.scoring.clean(0)
    page = _open(ui)
    page.eventDeleted.emit(0)
    assert ui.events.count(0) == 0
    assert ui.scoring.clean(0)
    assert page.count_labels[0].text() == "0"
