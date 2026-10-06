"""Report text from a Scoring: adaptation layer of the in-app sleep report. No Qt session."""

from export.export_sleep_report import _calculate_sleep_statistics
from scoring_model.scoring import Scoring

ALL = dict(sleep_stats=True, stage_distribution=True, latencies=True, awakenings=True, arousals=True)


def _scoring(stages):
    s = Scoring(len(stages), 30)
    for i, stage in enumerate(stages):
        s.set(i, stage)
    return s


def _text(stages, **opts):
    return _calculate_sleep_statistics(_scoring(stages), {**dict.fromkeys(ALL, False), **opts})


def test_numbers_and_percentages():
    text = _text([None, "Wake", "N2", "N2", "REM", "Wake"], sleep_stats=True, stage_distribution=True)
    assert "Total Sleep Time (TST):        1.5 min (0.0 h)" in text
    assert "Total Recording Time (TRT):    2.5 min (0.0 h)" in text
    assert "Sleep Efficiency:              60.0%" in text
    assert "N2:                            1.0 min (0.0 h) - 40.0%" in text


def test_inconclusive_neither_sleep_nor_wake():
    text = _text(["N2", "Inconclusive"], sleep_stats=True, stage_distribution=True)
    assert "Total Sleep Time (TST):        0.5 min" in text
    assert "Total Recording Time (TRT):    1.0 min" in text
    assert "Wake:                          0.0 min (0.0 h) - 0.0%" in text


def test_latencies_and_na():
    text = _text([None, "N2", "N2", "REM"], latencies=True)
    assert "N2 latency:                    0.5 min" in text
    assert "N3 latency:                    N/A" in text
    assert "REM latency:                   1.5 min" in text


def test_awakenings_average_duration():
    text = _text(["N3", "Wake", "Wake", "N2", "REM"], awakenings=True)
    assert f"{'N3 -> Wake:':<31}1" in text
    assert f"{'Avg. duration:':<31}1.0 min" in text


def test_arousals_from_stage_sequence():
    text = _text(["N3", "N1", "N2", "N1", "REM", None, "N1"], arousals=True)
    assert f"{'N3 -> N1:':<31}1" in text
    assert f"{'N2 -> N1:':<31}1" in text
    assert f"{'REM -> N1:':<31}1" in text
    assert f"{'Total:':<31}3" in text


def test_empty_scoring_does_not_fail():
    assert "Sleep Efficiency:              0.0%" in _text([None, None], sleep_stats=True)
