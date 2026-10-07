"""Open, save, import and config change on the primary/comparison Scoring via `loaded_ui`."""

import json
import os
import time

from PySide6 import QtWidgets

from scoring.scoring_import_comparison import scoring_import_comparison
from scoring.write_scoring import write_scoring
from scoring_model.formats import FORMATS
from scoring_model.scoring import Scoring

import config.apply_changes as apply_changes_module
import eeg.load_wrapper as load_wrapper_module
import scoring.scoring_import_comparison as comparison_module
from eeg.load_wrapper import load_wrapper


def _json(path):
    with open(path) as f:
        return json.load(f)


def test_example_file_round_trips_unchanged(loaded_ui):
    path = f"{loaded_ui.filename}.json"
    before = _json(path)
    write_scoring(loaded_ui)
    assert _json(path) == before
    assert loaded_ui.scoring.to_records() == before[0]


def test_events_are_kept_on_save(loaded_ui):
    path = f"{loaded_ui.filename}.json"
    events = _json(path)[1]
    loaded_ui.scoring.set(0, "N2", "human")
    write_scoring(loaded_ui)
    records, saved_events = _json(path)
    assert saved_events == events and records[0]["stage"] == "N2" and records[0]["digit"] == -2


def _write_short_file(ui, n):
    path = f"{ui.filename}.json"
    records = ui.scoring.to_records()[:n]
    with open(path, "w") as f:
        json.dump([records, [{"digit": 1, "event": "x", "start": 0, "end": 1, "epoch": [1], "key": "k", "counter": 0}]], f)
    return path


def test_mismatch_cancel_opens_empty_scoring_and_leaves_file(loaded_ui, monkeypatch):
    path = _write_short_file(loaded_ui, 5)
    before = open(path, "rb").read()
    monkeypatch.setattr(load_wrapper_module, "resolve_loaded", lambda *a: None)
    load_wrapper(loaded_ui, "eeglab")
    assert len(loaded_ui.scoring) == loaded_ui.numepo
    assert all(s is None for s in loaded_ui.scoring.stages())
    assert open(path, "rb").read() == before
    assert len(loaded_ui.AnnotationContainer[1].borders) == 1  # events survive for the first save


def test_mismatch_resolved_fits_recording(loaded_ui, monkeypatch):
    _write_short_file(loaded_ui, 5)
    seen = []
    monkeypatch.setattr(
        load_wrapper_module, "resolve_loaded",
        lambda parent, loaded, n, L: seen.append((len(loaded.stages), n)) or Scoring(n, L),
    )
    load_wrapper(loaded_ui, "eeglab")
    assert seen == [(5, loaded_ui.numepo)]
    assert len(loaded_ui.scoring) == loaded_ui.numepo


def test_missing_file_gives_empty_scoring(loaded_ui):
    os.remove(f"{loaded_ui.filename}.json")
    load_wrapper(loaded_ui, "eeglab")
    assert len(loaded_ui.scoring) == loaded_ui.numepo
    assert all(s is None for s in loaded_ui.scoring.stages())
    assert not os.path.exists(f"{loaded_ui.filename}.json")


def _import_comparison(ui, monkeypatch, tmp_path, name, resolve):
    path = str(tmp_path / "cmp")
    FORMATS[name].writer(ui.scoring, path)

    class Dialog:
        def exec(self):
            return True

        def selection(self):
            return FORMATS[name]

    monkeypatch.setattr(comparison_module, "_FormatDialog", Dialog)
    monkeypatch.setattr(comparison_module.QFileDialog, "getOpenFileName", lambda *a: (path, ""))
    monkeypatch.setattr(comparison_module, "resolve_loaded", resolve)
    scoring_import_comparison(ui)


def test_comparison_import_and_cancel(loaded_ui, monkeypatch, tmp_path):
    ui = loaded_ui
    end = time.time() + 120
    while not hasattr(ui, "swa") and time.time() < end:  # analysis data is built on a worker thread
        QtWidgets.QApplication.processEvents()
        time.sleep(0.01)
    ui.scoring.set(range(4), "N2")
    _import_comparison(ui, monkeypatch, tmp_path, "yasa", lambda parent, loaded, n, L: None)
    assert ui.scoring_comparison is None and not ui.action_remove_comparison.isEnabled()

    _import_comparison(ui, monkeypatch, tmp_path, "yasa",
                       lambda parent, loaded, n, L: Scoring(n, L))
    assert len(ui.scoring_comparison) == ui.numepo and ui.action_remove_comparison.isEnabled()


def test_epoch_length_change_creates_empty_scoring(loaded_ui, monkeypatch):
    ui = loaded_ui
    ui.scoring.set(0, "N2")
    monkeypatch.setattr(apply_changes_module, "settings_changed", lambda *a, **k: None)
    ui.config[0]["Epoch_length_s"] = 10
    apply_changes_module.apply_changes(["Epoch_length_s"], ui)
    assert len(ui.scoring) == ui.numepo and ui.scoring.epoch_length_s == 10
    assert all(s is None for s in ui.scoring.stages())
    assert ui.scoring_comparison is None
