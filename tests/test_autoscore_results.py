"""Tests for autoscorer result handling on an in-memory Scoring. No Qt, no session object."""

import numpy as np

from scoring.autoscore_results import apply_gssc, apply_nidra, apply_yasa, events_in_stages
from scoring_model.scoring import Scoring

CLASSES = ["Wake", "N1", "N2", "N3", "REM", "Artifact"]


def _probs(winners):
    """One-hot-ish probability matrix [n, 6] with a 0.8 winner column per epoch."""
    p = np.full((len(winners), 6), 0.04)
    for row, col in enumerate(winners):
        p[row, col] = 0.8
    return p


# ---- GSSC ------------------------------------------------------------------

def test_gssc_writes_stage_source_confidence_channels():
    s = Scoring(3, 30)
    probs = np.array([[0.7, 0.1, 0.1, 0.05, 0.05], [0.1, 0.2, 0.55, 0.1, 0.05], [0.1, 0.1, 0.1, 0.1, 0.60]])
    n = apply_gssc(s, np.array([0, 2, 4]), probs, ["C3", "EOG"])
    assert n == 3
    assert s.stages() == ["Wake", "N2", "REM"]
    assert [s.source(i) for i in range(3)] == ["GSSC"] * 3
    assert [s.confidence(i) for i in range(3)] == [0.7, 0.55, 0.6]
    assert s.channels(1) == ["C3", "EOG"]


def test_gssc_without_probabilities_has_no_confidence():
    s = Scoring(2, 30)
    apply_gssc(s, np.array([1, 3]), None, ["C3"])
    assert s.stages() == ["N1", "N3"] and s.confidence(0) is None


def test_gssc_midpoint_mapping_for_shorter_epochs():
    s = Scoring(6, 10)  # epochs 0-2 in model epoch 0, epochs 3-5 in model epoch 1
    apply_gssc(s, np.array([0, 3]), None, [])
    assert s.stages() == ["Wake"] * 3 + ["N3"] * 3


def test_gssc_midpoint_mapping_for_longer_epochs():
    s = Scoring(2, 60)  # midpoints 30 and 90 -> model epochs 1 and 3
    apply_gssc(s, np.array([0, 1, 2, 3]), None, [])
    assert s.stages() == ["N1", "N3"]


def test_gssc_midpoint_beyond_model_output_is_skipped():
    s = Scoring(4, 30)
    n = apply_gssc(s, np.array([2, 2]), None, [])
    assert n == 2 and s.stages() == ["N2", "N2", None, None]


def test_gssc_fill_missing_keeps_scored_epochs():
    s = Scoring(3, 30)
    s.set(1, "N3", source="human")
    apply_gssc(s, np.array([0, 0, 0]), None, [], mode="fill_missing")
    assert s.stages() == ["Wake", "N3", "Wake"] and s.source(1) == "human"


def test_gssc_selective_overwrites_only_selected_stages():
    s = Scoring(4, 30)
    s.set([0, 1, 2], ["N1", "N2", "REM"], source="human")
    apply_gssc(s, np.array([0, 0, 0, 0]), None, [], mode="selective", overwrite_stages={"N1", "REM"})
    assert s.stages() == ["Wake", "N2", "Wake", None]
    assert [s.source(i) for i in range(4)] == ["GSSC", "human", "GSSC", None]


# ---- NIDRA -----------------------------------------------------------------

def test_nidra_writes_stage_source_confidence_channels():
    s = Scoring(4, 30)
    hyp = np.array([0, 1, 5, 3])
    p = _probs([0, 1, 4, 3])
    artifacts = apply_nidra(s, hyp, p, CLASSES, "NIDRA (ez6)", ["C3", "C4"])
    assert artifacts == []
    assert s.stages() == ["Wake", "N1", "REM", "N3"]
    assert all(s.source(i) == "NIDRA (ez6)" for i in range(4))
    assert s.confidence(2) == 0.8 and s.channels(0) == ["C3", "C4"]
    assert all(s.clean(i) == 1 for i in range(4)) and s.probabilities(0) is None


def test_nidra_artifact_epoch_unscored_keeps_source_confidence_channels_and_is_unclean():
    s = Scoring(3, 30)
    s.set(1, "N2", source="human")
    artifacts = apply_nidra(s, np.array([2, 6, 2]), _probs([2, 5, 2]), CLASSES, "NIDRA (ez6)", ["C3"])
    assert artifacts == [[30, 60]]
    assert s.stage(1) is None and s.hypnogram_digit(1) is None
    assert s.source(1) == "NIDRA (ez6) — artifact"
    assert s.confidence(1) == 0.8 and s.channels(1) == ["C3"]
    assert s.clean(1) == 0 and s.clean(0) == 1


def test_nidra_artifact_epoch_as_inconclusive():
    s = Scoring(2, 30)
    apply_nidra(s, np.array([2, 6]), _probs([2, 5]), CLASSES, "NIDRA (ez6)", ["C3"],
                artifact_mode="inconclusive")
    assert s.stages() == ["N2", "Inconclusive"] and s.hypnogram_digit(1) == 2
    assert s.source(1) == "NIDRA (ez6) — artifact" and s.clean(1) == 0


def test_nidra_stores_probabilities_only_when_asked():
    s = Scoring(2, 30)
    p = _probs([0, 1])
    apply_nidra(s, np.array([0, 1]), p, CLASSES, "NIDRA", [], store_probabilities=True)
    assert s.probabilities(1) == {"Wake": 0.04, "N1": 0.8, "N2": 0.04, "N3": 0.04, "REM": 0.04, "Artifact": 0.04}
    apply_nidra(s, np.array([0, 1]), p, CLASSES, "NIDRA", [], store_probabilities=False)
    assert s.probabilities(1) is None


def test_nidra_artifact_marker_intervals_use_time_span_for_shorter_epochs():
    s = Scoring(4, 15)  # epochs 0,1 in model epoch 0; epochs 2,3 in model epoch 1 (artifact)
    artifacts = apply_nidra(s, np.array([2, 6]), _probs([2, 5]), CLASSES, "N", [])
    assert artifacts == [[30, 45], [45, 60]]
    assert [s.clean(i) for i in range(4)] == [1, 1, 0, 0]


def test_nidra_fill_missing_and_selective_modes():
    s = Scoring(3, 30)
    s.set([0, 1], ["N1", "N2"], source="human")
    apply_nidra(s, np.array([0, 0, 0]), _probs([0, 0, 0]), CLASSES, "N", [], mode="fill_missing")
    assert s.stages() == ["N1", "N2", "Wake"]
    s2 = Scoring(3, 30)
    s2.set([0, 1], ["N1", "N2"], source="human")
    apply_nidra(s2, np.array([0, 0, 0]), _probs([0, 0, 0]), CLASSES, "N", [],
                mode="selective", overwrite_stages={"N2"})
    assert s2.stages() == ["N1", "Wake", None]


def test_nidra_artifact_without_probability_column_has_no_confidence():
    s = Scoring(1, 30)
    apply_nidra(s, np.array([6]), np.full((1, 5), 0.2), CLASSES[:5], "N", [])
    assert s.confidence(0) is None


# ---- YASA ------------------------------------------------------------------

def test_yasa_maps_names_and_rounds_confidence():
    s = Scoring(3, 30)
    n = apply_yasa(s, np.array(["W", "N2", "R"]), np.array([0.123456, 0.9, 0.5]))
    assert n == 3
    assert s.stages() == ["Wake", "N2", "REM"]
    assert s.source(0) == "YASA" and s.confidence(0) == 0.1235 and s.channels(0) == []


# ---- detector stage filter -------------------------------------------------

def test_events_in_stages_keeps_events_by_midpoint_stage():
    s = Scoring(4, 30)
    s.set([0, 1, 2, 3], ["N2", "Wake", "N2", "N2"])
    events = [[1, 5], [28, 40], [35, 50], [80, 100], [200, 210]]
    # midpoints 3 (N2), 34 (Wake), 42.5 (Wake), 90 (N2), 205 (beyond scoring)
    assert events_in_stages(s, events, ["N2"]) == [[1, 5], [80, 100]]
    assert events_in_stages(s, events, []) == []
