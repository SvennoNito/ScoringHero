"""Event import and export dialogs on `loaded_ui`."""

import json
import os

import scoring.scoring_export_window as export_module
import scoring.scoring_import_window as import_module
from scoring.scoring_import_window import _merge_records
from scoring_model.event_records import artefact_flag_records, sleeptrip_event_records


def _epolen(ui):
    return ui.config[0]["Epoch_length_s"]


def test_artefact_flags_into_slot0_mark_unclean_and_other_slot_does_not(loaded_ui):
    ui, e = loaded_ui, _epolen(loaded_ui)
    flags = [0, 1, 1] + [0] * (ui.numepo - 3)
    ui.edit_events(lambda ev: ev.clear(0))
    ui.edit_events(lambda ev: _merge_records(ev, artefact_flag_records(flags, 0, "Artifact", e)))
    assert ui.events.artefact_epochs() == {1, 2}
    assert not ui.scoring.clean(1) and not ui.scoring.clean(2) and ui.scoring.clean(0)
    ui.edit_events(lambda ev: ev.clear(0))
    ui.edit_events(lambda ev: _merge_records(ev, artefact_flag_records(flags, 3, "F3", e)))
    assert ui.events.count(3) == 1 and ui.scoring.clean(1)


def test_sleeptrip_events_land_in_slot(loaded_ui):
    ui, e = loaded_ui, _epolen(loaded_ui)
    raw = [{"event": "x", "start": 0, "stop": e}]
    ui.edit_events(lambda ev: _merge_records(ev, sleeptrip_event_records(raw, 2, "x", e)))
    assert ui.events.label(2) == "x" and ui.events.spans(2) == [[0, e]]
    assert json.load(open(f"{ui.filename}.json"))[1]


def test_cancelled_export_keeps_name_and_writes_nothing(loaded_ui, monkeypatch):
    ui = loaded_ui
    name = ui.filename
    monkeypatch.setattr(export_module.QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
    monkeypatch.setattr(ui, "save_scoring", lambda: (_ for _ in ()).throw(AssertionError("wrote")))
    export_module.scoring_export_window(ui)
    assert ui.filename == name


def test_epoch_dialog_says_only_slot0_marks_artefacts(loaded_ui):
    d = import_module.EpochEventImportDialog()
    texts = " ".join(label.text() for label in d.findChildren(import_module.QLabel))
    assert "artefact" in texts and "slot A" in texts
