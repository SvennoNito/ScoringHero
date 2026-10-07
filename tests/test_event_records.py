"""Tests for the event record translator and the pure sleeptrip import conversions. No Qt."""

from scoring_model.event_records import (
    artefact_flag_records,
    events_from_records,
    events_to_records,
    sleeptrip_event_records,
)
from scoring_model.events import Events


def events_of():
    events = Events(30, 10)
    events.add(0, [(0, 30), (65, 100)])
    events.set_label(3, "Spindle")
    events.add(3, [(10, 20)])
    return events


def test_records_have_the_file_fields_with_one_based_epochs():
    assert events_to_records(events_of()) == [
        {"key": "A", "event": "Artifact", "digit": 0, "counter": 0, "epoch": [1], "start": 0, "end": 30},
        {"key": "A", "event": "Artifact", "digit": 0, "counter": 1, "epoch": [3, 4], "start": 65, "end": 100},
        {"key": "F3", "event": "Spindle", "digit": 3, "counter": 0, "epoch": [1], "start": 10, "end": 20},
    ]
    assert list(events_to_records(events_of())[0]) == ["key", "event", "digit", "counter", "epoch", "start", "end"]


def test_write_then_load_round_trips_spans_and_labels():
    loaded = events_from_records(events_to_records(events_of()), 30, 10)
    assert loaded.spans(0) == [[0, 30], [65, 100]]
    assert loaded.spans(3) == [[10, 20]]
    assert loaded.label(3) == "Spindle"
    assert loaded.artefact_epochs() == {0, 2, 3}


def test_old_file_loads_ignoring_stored_key_counter_and_epoch():
    old = [
        {"key": "zzz", "event": "Mine", "digit": 2, "counter": 7, "epoch": [99], "start": 31, "end": 40},
        {"key": "A", "event": "Mine", "digit": 2, "counter": 0, "epoch": [], "start": 0, "end": 5},
    ]
    events = events_from_records(old, 30, 10)
    assert events.spans(2) == [[0, 5], [31, 40]]
    assert events.label(2) == "Mine"
    assert events.epochs(2) == [[0], [1]]
    assert events_from_records(old[0:1], 30, 10).epochs(2) == [[1]]
    for record in old:
        del record["epoch"]  # missing epoch lists load too
    assert events_from_records(old, 30, 10).spans(2) == [[0, 5], [31, 40]]


def test_empty_events_and_unlabelled_slots():
    assert events_to_records(Events(30, 4)) == []
    assert events_from_records([], 30, 4).spans(1) == []


def test_sleeptrip_events_convert_to_records_for_a_slot():
    raw = [
        {"event": "spindle", "start": 40.0, "stop": 50.0, "duration": 10.0, "channel": "C3"},
        {"event": "spindle", "start": 10.0, "stop": 20.0, "duration": 10.0, "channel": "C3"},
    ]
    assert sleeptrip_event_records(raw, 4, "spindle", 30) == [
        {"key": "F4", "event": "spindle", "digit": 4, "counter": 0, "epoch": [1], "start": 10.0, "end": 20.0},
        {"key": "F4", "event": "spindle", "digit": 4, "counter": 1, "epoch": [2], "start": 40.0, "end": 50.0},
    ]
    assert sleeptrip_event_records([], 4, "x", 30) == []


def test_artefact_flags_convert_to_whole_epoch_records_for_a_slot():
    records = artefact_flag_records([0, 1, 1, 0, 1], 0, "Artifact", 30)
    assert [(r["digit"], r["key"], r["start"], r["end"], r["epoch"]) for r in records] == [
        (0, "A", 30, 90, [2, 3]),
        (0, "A", 120, 150, [5]),
    ]
    assert artefact_flag_records([0, 0], 5, "Flag", 30) == []
