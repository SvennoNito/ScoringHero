"""The Event detector GUI function, driven through the headless app with a fake detector."""

import json

import numpy as np
import pytest

import event_detection.run_detector_gui as gui
from event_detection.run_detector import DetectorSpec, DetectorUnavailable, events_in_stages
from scoring_model.scoring import Scoring


class Dialogs:
    def __init__(self):
        self.errors = []

    def critical(self, parent, title, text):
        self.errors.append((title, text))


@pytest.fixture
def dialogs(monkeypatch):
    d = Dialogs()
    monkeypatch.setattr(gui.QMessageBox, "critical", staticmethod(d.critical))
    return d


@pytest.fixture
def ui(loaded_ui):
    loaded_ui.scoring = Scoring(loaded_ui.numepo, loaded_ui.config[0]["Epoch_length_s"])
    return loaded_ui


def make_spec(detect):
    return DetectorSpec(detect=detect, args=lambda s: {}, method="Fake", title="Fake", noun="thing")


def settings_for(ui, **extra):
    return {
        "channel": ui.config[1][1]["Channel_name"],
        "marker": ui.AnnotationContainer[0].label,
        **extra,
    }


def saved_starts(ui):
    with open(f"{ui.filename}.json") as f:
        data = json.load(f)
    return sorted(
        e["start"] for e in _find_events(data)
    )


def _find_events(node):
    if isinstance(node, dict):
        if "start" in node and "end" in node and "event" in node:
            yield node
        for v in node.values():
            yield from _find_events(v)
    elif isinstance(node, list):
        for v in node:
            yield from _find_events(v)


def test_selected_channel_signal_reaches_detector_as_float64(ui, dialogs):
    seen = {}

    def detect(signal, sfreq):
        seen.update(signal=signal, sfreq=sfreq)
        return []

    assert gui.run_event_detector(ui, make_spec(detect), settings_for(ui))
    assert seen["signal"].dtype == np.float64
    assert np.array_equal(seen["signal"], ui.eeg_data_display[1])
    assert seen["sfreq"] == float(ui.config[0]["Sampling_rate_hz"])


def test_unknown_channel_shows_error_and_adds_no_events(ui, dialogs):
    called = []
    spec = make_spec(lambda signal, sfreq: called.append(1) or [[0, 1]])
    assert not gui.run_event_detector(ui, spec, settings_for(ui, channel="nope"))
    assert not called
    assert dialogs.errors and dialogs.errors[0][0] == "Fake Error"
    assert ui.AnnotationContainer[0].borders == []


def test_stage_filter_keeps_only_events_in_chosen_stages(ui, dialogs):
    ui.scoring.set([0], ["N2"])
    ui.scoring.set([1], ["Wake"])
    spec = make_spec(lambda signal, sfreq: [[1, 5], [31, 35]])
    assert gui.run_event_detector(ui, spec, settings_for(ui, filter_stages=["N2"]))
    assert ui.AnnotationContainer[0].borders == [[1, 5]]


def test_no_chosen_stages_keeps_all_events(ui, dialogs):
    spec = make_spec(lambda signal, sfreq: [[1, 5], [31, 35]])
    assert gui.run_event_detector(ui, spec, settings_for(ui, filter_stages=[]))
    assert ui.AnnotationContainer[0].borders == [[1, 5], [31, 35]]


def test_events_land_in_chosen_container_and_are_saved(ui, dialogs):
    container = ui.AnnotationContainer[-1]
    spec = make_spec(lambda signal, sfreq: [[2, 4]])
    assert gui.run_event_detector(ui, spec, settings_for(ui, marker=container.label))
    assert container.borders == [[2, 4]]
    assert saved_starts(ui) == [2]
    assert all(c.borders == [] for c in ui.AnnotationContainer[:-1])


def test_detector_exception_shows_error_without_crashing(ui, dialogs):
    def detect(signal, sfreq):
        raise RuntimeError("boom")

    assert not gui.run_event_detector(ui, make_spec(detect), settings_for(ui))
    title, text = dialogs.errors[0]
    assert title == "Fake Error" and "boom" in text


def test_detector_unavailable_shows_its_own_title_and_message(ui, dialogs):
    def detect(signal, sfreq):
        raise DetectorUnavailable("Fake Not Installed", "pip install fake")

    assert not gui.run_event_detector(ui, make_spec(detect), settings_for(ui))
    assert dialogs.errors == [("Fake Not Installed", "pip install fake")]


def test_events_in_stages_keeps_events_by_midpoint_stage():
    s = Scoring(4, 30)
    s.set([0, 1, 2, 3], ["N2", "Wake", "N2", "N2"])
    events = [[1, 5], [28, 40], [35, 50], [80, 100], [200, 210]]
    # midpoints 3 (N2), 34 (Wake), 42.5 (Wake), 90 (N2), 205 (beyond scoring)
    assert events_in_stages(s, events, ["N2"]) == [[1, 5], [80, 100]]
    assert events_in_stages(s, events, []) == []
