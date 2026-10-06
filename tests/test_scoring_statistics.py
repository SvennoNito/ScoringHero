"""Tests for sleep statistics of a Scoring (numbers only). No Qt, no session object."""

import pytest

from scoring_model.scoring import Scoring
from scoring_model.statistics import sleep_statistics


def _scoring(stages, epoch_length_s=30):
    s = Scoring(len(stages), epoch_length_s)
    for i, stage in enumerate(stages):
        s.set(i, stage)
    return s


W, N1, N2, N3, R, INC, U = "Wake", "N1", "N2", "N3", "REM", "Inconclusive", None

# 30 s epochs; indices 0..13; 12 scored (leading and trailing unscored)
TYPICAL = [U, W, W, N1, N2, N2, N3, W, N2, R, W, W, INC, U]


def test_typical_stage_counts_and_times():
    st = sleep_statistics(_scoring(TYPICAL))
    assert st.stage_counts == {"Wake": 5, "N1": 1, "N2": 3, "N3": 1, "REM": 1, "Inconclusive": 1}
    assert st.scored_epochs == 12
    assert st.total_sleep_min == 3.0  # N1 + N2 + N3 + REM = 6 epochs
    assert st.total_recording_min == 6.0  # scored epochs, Inconclusive included
    assert st.efficiency == 50.0


def test_typical_latencies_count_from_recording_start_including_unscored():
    st = sleep_statistics(_scoring(TYPICAL))
    assert st.latency_min == {"N2": 2.0, "N3": 3.0, "REM": 4.5}


def test_typical_awakenings_by_previous_stage():
    # N3 -> Wake at epoch 7 counts; the final Wake run follows the last sleep epoch
    st = sleep_statistics(_scoring(TYPICAL))
    assert st.awakenings == {"N3": 1, "N2": 0, "REM": 0}
    assert st.awakening_durations_min == [0.5]


def test_awakenings_by_previous_stage_and_durations():
    #        N2  W  W  N2  REM  W  N3  W  W  W  N2  W(after last sleep)
    stages = [N2, W, W, N2, R, W, N3, W, W, W, N2, W]
    st = sleep_statistics(_scoring(stages, epoch_length_s=60))
    assert st.awakenings == {"N3": 1, "N2": 1, "REM": 1}
    assert st.awakening_durations_min == [2.0, 1.0, 3.0]


def test_awakening_from_n1_is_not_counted():
    st = sleep_statistics(_scoring([N2, N1, W, N2, N2]))
    assert st.awakenings == {"N3": 0, "N2": 0, "REM": 0}
    assert st.awakening_durations_min == []


def test_awakenings_transition_across_unscored_epochs():
    # unscored epochs are skipped: N3, unscored, Wake is an N3 -> Wake transition
    st = sleep_statistics(_scoring([N3, U, U, W, N2]))
    assert st.awakenings == {"N3": 1, "N2": 0, "REM": 0}


def test_wake_only_after_last_sleep_is_no_awakening():
    st = sleep_statistics(_scoring([N2, N2, W, W]))
    assert st.awakenings == {"N3": 0, "N2": 0, "REM": 0}


def test_inconclusive_is_neither_sleep_nor_wake_but_in_scored_total():
    # 2 wake, 2 N2, 2 inconclusive, 2 unscored -> scored = 6
    st = sleep_statistics(_scoring([W, W, N2, N2, INC, INC, U, U], epoch_length_s=60))
    assert st.stage_counts["Wake"] == 2
    assert st.stage_counts["Inconclusive"] == 2
    assert st.scored_epochs == 6
    assert st.total_sleep_min == 2.0
    assert st.total_recording_min == 6.0
    assert st.efficiency == pytest.approx(100 / 3)


def test_inconclusive_between_sleep_and_wake_breaks_the_awakening():
    # N2, Inconclusive, Wake: the previous stage of Wake is Inconclusive, not sleep
    st = sleep_statistics(_scoring([N2, INC, W, N2]))
    assert st.awakenings == {"N3": 0, "N2": 0, "REM": 0}


def test_inconclusive_only_has_no_sleep_and_no_latency():
    st = sleep_statistics(_scoring([INC, INC]))
    assert st.scored_epochs == 2
    assert (st.total_sleep_min, st.total_recording_min, st.efficiency) == (0.0, 1.0, 0.0)
    assert st.latency_min == {"N2": None, "N3": None, "REM": None}


def test_missing_stage_has_no_latency():
    st = sleep_statistics(_scoring([W, N1, N2, N2]))
    assert st.latency_min == {"N2": 1.0, "N3": None, "REM": None}


def test_epoch_length_scales_minutes():
    stages = [W, N2, N2, N2]
    assert sleep_statistics(_scoring(stages, 30)).total_sleep_min == 1.5
    assert sleep_statistics(_scoring(stages, 20)).total_sleep_min == 1.0
    assert sleep_statistics(_scoring(stages, 20)).latency_min["N2"] == pytest.approx(1 / 3)


def test_all_unscored_scoring():
    st = sleep_statistics(Scoring(5, 30))
    assert st.stage_counts == {"Wake": 0, "N1": 0, "N2": 0, "N3": 0, "REM": 0, "Inconclusive": 0}
    assert (st.scored_epochs, st.total_sleep_min, st.total_recording_min, st.efficiency) == (0, 0.0, 0.0, 0.0)
    assert st.latency_min == {"N2": None, "N3": None, "REM": None}
    assert st.awakenings == {"N3": 0, "N2": 0, "REM": 0}
    assert st.awakening_durations_min == []


def test_empty_scoring():
    st = sleep_statistics(Scoring(0, 30))
    assert st.scored_epochs == 0 and st.efficiency == 0.0 and st.total_recording_min == 0.0
    assert st.latency_min == {"N2": None, "N3": None, "REM": None}


def test_statistics_do_not_modify_scoring():
    s = _scoring(TYPICAL)
    before = s.to_records()
    sleep_statistics(s)
    assert s.to_records() == before
