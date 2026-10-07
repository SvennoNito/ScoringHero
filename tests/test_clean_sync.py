"""Tests for the lossless artefact-to-clean sync. Real Scoring and Events, no Qt."""

from scoring_model.clean_sync import sync_clean
from scoring_model.events import ARTEFACT_SLOT, Events
from scoring_model.scoring import Scoring


def make():
    return Scoring(10, 30), Events(30, 10)


def unclean(scoring):
    return {i for i in range(10) if not scoring.clean(i)}


def edit(scoring, events, spans):
    """Replace slot 0 by `spans`, then sync from the epochs before the edit."""
    before = events.artefact_epochs()
    events.add(ARTEFACT_SLOT, spans)
    sync_clean(scoring, before, events.artefact_epochs())


def test_newly_covered_epochs_become_unclean():
    scoring, events = make()
    edit(scoring, events, [(60, 120)])
    assert unclean(scoring) == {2, 3}


def test_newly_uncovered_epochs_become_clean():
    scoring, events = make()
    edit(scoring, events, [(60, 120)])
    before = events.artefact_epochs()
    events.clear(ARTEFACT_SLOT)
    sync_clean(scoring, before, events.artefact_epochs())
    assert unclean(scoring) == set()


def test_unrelated_unclean_epochs_survive():
    scoring, events = make()
    scoring.set_clean([8], 0)  # e.g. from an old file
    edit(scoring, events, [(0, 30)])
    assert unclean(scoring) == {0, 8}


def test_unrelated_clean_epochs_stay_clean_when_uncovered():
    scoring, events = make()
    scoring.set_clean([0, 1], 0)
    sync_clean(scoring, {0}, set())
    assert unclean(scoring) == {1}


def test_empty_before_marks_all_covered_epochs_unclean():
    scoring, events = make()
    events.add(ARTEFACT_SLOT, [(30, 90), (240, 270)])
    sync_clean(scoring, set(), events.artefact_epochs())
    assert unclean(scoring) == {1, 2, 8}
