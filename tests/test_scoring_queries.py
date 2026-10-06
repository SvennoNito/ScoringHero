"""Tests for Scoring queries (next unscored / uncertain / human / transition /
disagreement) and on-demand disagreements. No Qt, no session object."""

import pytest

from scoring_model.scoring import Scoring, disagreements


def _scoring(stages, **per_epoch):
    """Scoring from stage names (None = unscored); source/confidence per epoch by keyword."""
    s = Scoring(len(stages), 30)
    for i, stage in enumerate(stages):
        s.set(i, stage, source=per_epoch.get("source", [None] * len(stages))[i],
              confidence=per_epoch.get("confidence", [None] * len(stages))[i])
    return s


# ---- next unscored --------------------------------------------------------

def test_next_unscored_finds_following_epoch():
    s = _scoring(["N2", None, "N2", None, "N2"])
    assert s.next_unscored(0) == 1
    assert s.next_unscored(1) == 3


def test_next_unscored_wraps_around_from_last_epoch():
    s = _scoring([None, "N2", "N2", "N2"])
    assert s.next_unscored(3) == 0
    assert s.next_unscored(1) == 0


def test_next_unscored_none_when_all_scored():
    assert _scoring(["N2", "Wake", "REM"]).next_unscored(1) is None


def test_next_unscored_single_match_is_found_from_every_epoch_including_itself():
    s = _scoring(["N2", None, "N2"])
    assert [s.next_unscored(i) for i in range(3)] == [1, 1, 1]


def test_next_unscored_on_all_unscored_is_the_following_epoch():
    s = Scoring(3, 30)
    assert [s.next_unscored(i) for i in range(3)] == [1, 2, 0]


def test_inconclusive_is_scored():
    assert _scoring(["Inconclusive", "Inconclusive"]).next_unscored(0) is None


# ---- next uncertain -------------------------------------------------------

def test_next_uncertain_is_confidence_below_half():
    s = _scoring(["N2"] * 5, confidence=[0.9, 0.49, 0.5, 0.1, None])
    assert s.next_uncertain(0) == 1
    assert s.next_uncertain(1) == 3  # 0.5 is not uncertain, None is not uncertain


def test_next_uncertain_wraps_around():
    s = _scoring(["N2"] * 4, confidence=[0.2, 0.9, 0.9, 0.9])
    assert s.next_uncertain(2) == 0


def test_next_uncertain_none_when_nothing_below_half():
    s = _scoring(["N2"] * 3, confidence=[0.5, 0.9, None])
    assert s.next_uncertain(0) is None


def test_next_uncertain_single_match_is_itself_when_current():
    s = _scoring(["N2"] * 3, confidence=[0.9, 0.1, 0.9])
    assert s.next_uncertain(1) == 1


# ---- next human -----------------------------------------------------------

def test_next_human_is_source_human():
    s = _scoring(["N2"] * 4, source=["YASA", "human", "GSSC", "human"])
    assert s.next_human(0) == 1
    assert s.next_human(1) == 3


def test_next_human_wraps_around():
    s = _scoring(["N2"] * 3, source=["human", "YASA", "YASA"])
    assert s.next_human(2) == 0


def test_next_human_none_when_no_human_epoch():
    s = _scoring(["N2"] * 3, source=["YASA", None, "GSSC"])
    assert s.next_human(0) is None


def test_next_human_single_match_is_itself_when_current():
    s = _scoring(["N2"] * 3, source=["YASA", "human", "YASA"])
    assert s.next_human(1) == 1


# ---- next transition ------------------------------------------------------

def test_next_transition_is_next_epoch_with_different_stage():
    s = _scoring(["Wake", "Wake", "N1", "N1", "N2"])
    assert s.next_transition(0) == 2
    assert s.next_transition(2) == 4


def test_next_transition_from_middle_of_a_run_goes_to_end_of_run():
    s = _scoring(["N2", "N2", "N2", "REM"])
    assert s.next_transition(1) == 3


def test_next_transition_wraps_around():
    s = _scoring(["Wake", "N2", "N2", "N2"])
    assert s.next_transition(2) == 0
    assert s.next_transition(3) == 0


def test_next_transition_none_when_stage_never_changes():
    assert _scoring(["N2"] * 4).next_transition(1) is None
    assert Scoring(4, 30).next_transition(1) is None  # all unscored


def test_next_transition_between_unscored_and_scored():
    s = _scoring([None, None, "N2"])
    assert s.next_transition(0) == 2


# ---- queries on degenerate scorings ----------------------------------------

def test_queries_on_empty_scoring_return_none():
    s = Scoring(0, 30)
    assert s.next_unscored(0) is None
    assert s.next_uncertain(0) is None
    assert s.next_human(0) is None
    assert s.next_transition(0) is None
    assert s.next_disagreement(0, Scoring(0, 30)) is None


def test_queries_reject_out_of_range_epoch():
    s = Scoring(3, 30)
    with pytest.raises(IndexError):
        s.next_unscored(3)
    with pytest.raises(IndexError):
        s.next_transition(-1)


def test_queries_do_not_modify_scoring():
    s = _scoring(["N2", None, "Wake"], source=["human", None, "YASA"])
    before = s.to_records()
    s.next_unscored(0), s.next_uncertain(0), s.next_human(0), s.next_transition(0)
    assert s.to_records() == before


# ---- disagreements --------------------------------------------------------

def test_disagreements_lists_epochs_with_different_stage():
    a = _scoring(["Wake", "N1", "N2", "N3", "REM"])
    b = _scoring(["Wake", "N2", "N2", "REM", "REM"])
    assert disagreements(a, b) == [1, 3]


def test_disagreements_ignore_source_confidence_and_channels():
    a = Scoring(2, 30)
    b = Scoring(2, 30)
    a.set([0, 1], "N2", source="human", channels=["C3"])
    b.set([0, 1], "N2", source="YASA", confidence=0.1, channels=["C4"])
    assert disagreements(a, b) == []


def test_disagreement_between_scored_and_unscored_but_not_between_two_unscored():
    a = _scoring(["N2", None, None])
    b = _scoring([None, "N2", None])
    assert disagreements(a, b) == [0, 1]


def test_disagreements_empty_scorings():
    assert disagreements(Scoring(0, 30), Scoring(0, 30)) == []


def test_disagreements_reflect_edits_after_comparison_was_set():
    primary = _scoring(["N2", "N2", "N2"])
    comparison = _scoring(["N2", "Wake", "N2"])
    assert disagreements(primary, comparison) == [1]
    primary.set(1, "Wake", source="human")
    assert disagreements(primary, comparison) == []
    primary.set(2, "REM", source="human")
    assert disagreements(primary, comparison) == [2]
    comparison.set(2, "REM")
    assert disagreements(primary, comparison) == []


def test_disagreements_of_different_length_scorings_raise():
    with pytest.raises(ValueError):
        disagreements(Scoring(3, 30), Scoring(4, 30))


# ---- next disagreement ----------------------------------------------------

def test_next_disagreement_follows_current_epoch():
    a = _scoring(["N2"] * 5)
    b = _scoring(["N2", "Wake", "N2", "REM", "N2"])
    assert a.next_disagreement(0, b) == 1
    assert a.next_disagreement(1, b) == 3


def test_next_disagreement_wraps_around():
    a = _scoring(["N2"] * 4)
    b = _scoring(["Wake", "N2", "N2", "N2"])
    assert a.next_disagreement(3, b) == 0
    assert a.next_disagreement(1, b) == 0


def test_next_disagreement_none_when_scorings_agree():
    a = _scoring(["N2", None, "REM"])
    assert a.next_disagreement(0, _scoring(["N2", None, "REM"])) is None


def test_next_disagreement_single_match_is_itself_when_current():
    a = _scoring(["N2"] * 3)
    b = _scoring(["N2", "REM", "N2"])
    assert [a.next_disagreement(i, b) for i in range(3)] == [1, 1, 1]


def test_next_disagreement_uses_current_edits():
    a = _scoring(["N2"] * 3)
    b = _scoring(["N2", "REM", "N2"])
    a.set(1, "REM", source="human")
    assert a.next_disagreement(0, b) is None


def test_next_disagreement_length_mismatch_raises():
    with pytest.raises(ValueError):
        Scoring(3, 30).next_disagreement(0, Scoring(2, 30))
