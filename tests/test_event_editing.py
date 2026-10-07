"""Event editing through the headless app: the Events module on the main window, the GUI
step after every edit, file round trip and epoch-length change."""

import json

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

import config.apply_changes as apply_changes_module
import paint_event.rectangle_events as rectangle_events
import scoringhero as sh
import ui.setup_ui as setup_ui_module
from eeg.load_wrapper import load_wrapper
from scoring_model.events import N_SLOTS
from utilities.jump_to_event import jump_to_event


def _file(ui):
    with open(f"{ui.filename}.json") as f:
        return json.load(f)


def _file_events(ui, slot):
    return [(e["start"], e["end"], e["epoch"]) for e in _file(ui)[1] if e["digit"] == slot]


def _clear_all_events(ui):
    for slot in range(N_SLOTS):
        ui.edit_events(lambda events, slot=slot: events.clear(slot))


def _draw(ui, start_s, end_s):
    """Pretend the user dragged a rectangle over [start_s, end_s] of the signal panel."""
    vb = ui.SignalWidget.axes.plotItem.vb
    ui.PaintEventWidget.stored_corners = [[vb.mapViewToScene(QPointF(start_s, 0)), vb.mapViewToScene(QPointF(end_s, 1))]]


def test_main_window_starts_with_all_slots():
    QApplication.instance() or QApplication([])
    ui = sh.Ui_MainWindow()
    assert all(ui.events.label(slot) for slot in range(N_SLOTS))
    assert ui.events.count(10) == ui.events.count(12) == 0


def test_hotkey_action_toggles_epoch_and_writes_file(loaded_ui):
    ui = loaded_ui
    _clear_all_events(ui)
    length = ui.config[0]["Epoch_length_s"]
    ui.this_epoch = 2
    ui.action_F10.trigger()
    assert ui.events.spans(10) == [[2 * length, 3 * length]]
    assert _file_events(ui, 10) == [(2 * length, 3 * length, [3])]
    ui.action_F10.trigger()
    assert ui.events.spans(10) == [] and _file_events(ui, 10) == []


def test_events_survive_reload(loaded_ui, wait_loaded):
    ui = loaded_ui
    _clear_all_events(ui)
    ui.this_epoch = 1
    ui.action_F3.trigger()
    ui.this_epoch = 4
    ui.action_F12.trigger()
    spans = {slot: ui.events.spans(slot) for slot in range(N_SLOTS)}
    load_wrapper(ui, "eeglab")
    wait_loaded(ui)
    assert {slot: ui.events.spans(slot) for slot in range(N_SLOTS)} == spans
    assert spans[3] and spans[12]


def test_artefact_edits_mark_and_unmark_exactly_the_covered_epochs(loaded_ui):
    ui = loaded_ui
    _clear_all_events(ui)
    ui.scoring.set_clean([7], 0)  # an unclean flag no event covers survives
    ui.this_epoch = 2
    ui.action_artefact.trigger()
    assert not ui.scoring.clean(2) and ui.scoring.clean(3) and not ui.scoring.clean(7)
    ui.action_artefact.trigger()
    assert ui.scoring.clean(2) and not ui.scoring.clean(7)
    assert [r["clean"] for r in _file(ui)[0]][2] == 1


def test_drawn_rectangle_is_clipped_to_the_displayed_range(loaded_ui):
    ui = loaded_ui
    _clear_all_events(ui)
    ui.this_epoch = 1
    lo = ui.times[1][0][0]
    _draw(ui, lo + 1, lo + 3)
    ui.action_F2.trigger()
    (start, end), = ui.events.spans(2)
    assert abs(start - (lo + 1)) < 0.05 and abs(end - (lo + 3)) < 0.05
    assert ui.PaintEventWidget.stored_corners == []
    _draw(ui, lo - 50, lo + 4)
    ui.action_F2.trigger()
    assert ui.events.spans(2)[0][0] >= lo - 1e-6 and ui.events.spans(2)[0][1] > end


def test_erase_in_drawn_rectangle_and_delete_in_epoch(loaded_ui):
    ui = loaded_ui
    _clear_all_events(ui)
    length = ui.config[0]["Epoch_length_s"]
    ui.this_epoch = 1
    ui.action_F1.trigger()
    ui.action_F4.trigger()
    ui.this_epoch = 2
    ui.action_F4.trigger()
    _draw(ui, length + 10, length + 20)
    rectangle_events.erase_events_in_rectangles(ui)
    assert ui.PaintEventWidget.stored_corners == []
    for slot in (1, 4):
        assert len(ui.events.spans(slot)) >= 1
    assert all(not start < length + 15 < end for slot in (1, 4) for start, end in ui.events.spans(slot))
    assert _file_events(ui, 1)
    setup_ui_module._delete_events_in_current_epoch(ui)
    assert ui.events.events_in_epoch(2) == []
    assert ui.events.spans(4) != [] and ui.events.events_in_epoch(1)


def test_relabel_and_drop_through_the_gui_step(loaded_ui):
    ui = loaded_ui
    _clear_all_events(ui)
    length = ui.config[0]["Epoch_length_s"]
    ui.this_epoch = 1
    ui.action_F1.trigger()
    ui.action_F2.trigger()
    click = length + 5
    assert ui.edit_events(lambda events: events.relabel(click, 6))
    assert ui.events.spans(6) and _file_events(ui, 6)
    assert ui.events.spans(1) == [] and ui.events.spans(2)  # relabel moved the slot-1 event
    ui.edit_events(lambda events: events.drop(click))
    assert all(ui.events.count(slot) == 0 for slot in range(N_SLOTS))
    assert not _file_events(ui, 6) and not _file_events(ui, 2)


def test_hypnogram_markers_and_jump_follow_the_events(loaded_ui):
    ui = loaded_ui
    _clear_all_events(ui)
    assert ui.HypnogramWidget.event_items == []
    ui.this_epoch = 5
    ui.action_F3.trigger()
    ui.action_F7.trigger()
    assert len(ui.HypnogramWidget.event_items) == 2
    ui.this_epoch = 0
    jump_to_event(ui)
    assert ui.this_epoch == 5
    ui.action_F3.trigger()
    ui.action_F7.trigger()
    assert ui.HypnogramWidget.event_items == []


def test_epoch_length_change_keeps_events_and_syncs_clean(loaded_ui, monkeypatch):
    ui = loaded_ui
    _clear_all_events(ui)
    ui.edit_events(lambda events: events.add(0, [(30, 60)]))
    ui.edit_events(lambda events: events.add(1, [(5, 25)]))
    monkeypatch.setattr(apply_changes_module, "settings_changed", lambda *a, **k: None)
    ui.config[0]["Epoch_length_s"] = 10
    apply_changes_module.apply_changes(["Epoch_length_s"], ui)
    assert ui.events.spans(0) == [[30, 60]] and ui.events.spans(1) == [[5, 25]]
    assert ui.events.epochs(0) == [[3, 4, 5]] and ui.events.epochs(1) == [[0, 1, 2]]
    assert [i for i in range(ui.numepo) if not ui.scoring.clean(i)] == [3, 4, 5]
