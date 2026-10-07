"""Tests for the Scoring module: stage table, per-epoch data, bulk set, time span,
records conversion and length fitting. No Qt, no session object."""

import json

import pytest

from scoring_model.scoring import STAGE_DIGITS, Scoring, stage_digit, unknown_stages

RECORD_KEYS = ["epoch", "start", "end", "stage", "digit", "confidence", "channels", "clean", "source"]


def test_stage_table_has_every_stage_once_and_no_nrem():
    assert STAGE_DIGITS == {"Wake": 1, "N1": -1, "N2": -2, "N3": -3, "REM": 0, "Inconclusive": 2}
    assert stage_digit(None) is None
    assert stage_digit("N2") == -2


def test_new_scoring_is_unscored():
    s = Scoring(3, 30)
    assert len(s) == 3
    assert s.stages() == [None, None, None]
    assert s.digit(1) is None
    assert s.source(1) is None
    assert s.confidence(1) is None
    assert s.channels(1) == []
    assert s.clean(1) == 1


def test_getters_reject_out_of_range_epochs():
    s = Scoring(3, 30)
    for bad in (-1, 3):
        with pytest.raises(IndexError):
            s.stage(bad)


def test_time_span_uses_zero_based_index_and_epoch_length():
    s = Scoring(4, 20)
    assert s.time_span(0) == (0, 20)
    assert s.time_span(3) == (60, 80)


def test_set_one_epoch():
    s = Scoring(3, 30)
    s.set(1, "N2", source="human", channels=["C3", "C4"])
    assert (s.stage(1), s.digit(1), s.source(1), s.channels(1)) == ("N2", -2, "human", ["C3", "C4"])
    assert s.stage(0) is None and s.stage(2) is None


def test_set_many_epochs_same_values():
    s = Scoring(5, 30)
    s.set([1, 2, 4], "REM", source="YASA", confidence=0.9)
    assert s.stages() == [None, "REM", "REM", None, "REM"]
    assert s.source(4) == "YASA" and s.confidence(2) == 0.9 and s.confidence(0) is None


def test_set_many_epochs_per_epoch_values():
    s = Scoring(4, 30)
    s.set(range(1, 4), ["Wake", "N1", "N3"], source="GSSC", confidence=[0.5, 0.6, 0.7])
    assert s.stages() == [None, "Wake", "N1", "N3"]
    assert [s.confidence(i) for i in range(1, 4)] == [0.5, 0.6, 0.7]


def test_set_channels_are_copied_per_epoch():
    s = Scoring(2, 30)
    chans = ["C3"]
    s.set([0, 1], "N1", channels=chans)
    chans.append("C4")
    s.channels(0).append("x")
    assert s.channels(0) == ["C3"] and s.channels(1) == ["C3"]


def test_set_rejects_unknown_stage_and_wrong_length_sequences():
    s = Scoring(2, 30)
    with pytest.raises(ValueError):
        s.set(0, "Bogus")
    with pytest.raises(ValueError):
        s.set([0, 1], ["N1"])
    assert s.stages() == [None, None]


def test_clearing_stage_clears_source_confidence_channels():
    s = Scoring(2, 30)
    s.set([0, 1], "N2", source="YASA", confidence=0.8, channels=["C3"])
    s.set(0, None)
    assert (s.stage(0), s.source(0), s.confidence(0), s.channels(0)) == (None, None, None, [])
    assert s.source(1) == "YASA"


def test_unscored_epoch_keeps_explicitly_passed_source_confidence_channels():
    s = Scoring(1, 30)
    s.set(0, "N2", source="YASA")
    s.set(0, None, source="artefact", confidence=0.4, channels=["C3"])
    assert (s.stage(0), s.source(0), s.confidence(0), s.channels(0)) == (None, "artefact", 0.4, ["C3"])
    s.set(0, None)
    assert (s.source(0), s.confidence(0), s.channels(0)) == (None, None, [])


def test_clearing_stage_keeps_clean_flag():
    s = Scoring(1, 30)
    s.set(0, "N2")
    s.set_clean(0, False)
    s.set(0, None)
    assert s.clean(0) == 0


def test_clean_flag_one_and_many_epochs():
    s = Scoring(4, 30)
    s.set_clean(2, False)
    assert [s.clean(i) for i in range(4)] == [1, 1, 0, 1]
    s.set_clean([0, 1, 2], 0)
    assert [s.clean(i) for i in range(4)] == [0, 0, 0, 1]
    s.set_clean(range(4), True)
    assert [s.clean(i) for i in range(4)] == [1, 1, 1, 1]


def test_records_of_unscored_match_the_file_format():
    assert Scoring(2, 30).to_records() == [
        {"epoch": 1, "start": 0, "end": 30, "stage": None, "digit": None, "confidence": None,
         "channels": [], "clean": 1, "source": None},
        {"epoch": 2, "start": 30, "end": 60, "stage": None, "digit": None, "confidence": None,
         "channels": [], "clean": 1, "source": None},
    ]


def test_records_write_digit_and_compute_epoch_start_end():
    s = Scoring(3, 20)
    s.set(2, "N3", source="human", channels=["C3"])
    rec = s.to_records()[2]
    assert list(rec) == RECORD_KEYS
    assert (rec["epoch"], rec["start"], rec["end"]) == (3, 40, 60)
    assert (rec["stage"], rec["digit"], rec["source"], rec["channels"]) == ("N3", -3, "human", ["C3"])


def test_records_are_json_serialisable():
    s = Scoring(2, 30)
    s.set(0, "REM", source="NIDRA", confidence=0.25)
    json.dumps(s.to_records())


def test_records_round_trip():
    s = Scoring(4, 30)
    s.set([0, 1], ["Wake", "Inconclusive"], source="GSSC", confidence=[0.9, 0.4], channels=["C3"])
    s.set(2, "N2", source="human")
    s.set_clean(2, False)
    again = Scoring.from_records(json.loads(json.dumps(s.to_records())), 30)
    assert again.to_records() == s.to_records()
    assert again.clean(2) == 0


def test_digit_in_records_is_ignored_stage_name_wins():
    rec = Scoring(1, 30).to_records()
    rec[0].update(stage="N1", digit=2, epoch=99, start=5, end=6)
    s = Scoring.from_records(rec, 30)
    assert s.stage(0) == "N1" and s.digit(0) == -1
    assert s.to_records()[0]["digit"] == -1
    assert (s.to_records()[0]["epoch"], s.to_records()[0]["start"]) == (1, 0)


def test_records_with_missing_or_null_fields_load_with_defaults():
    s = Scoring.from_records([{"stage": "N2", "channels": None}, {"stage": None, "digit": None}], 30)
    assert s.stages() == ["N2", None]
    assert s.channels(0) == [] and s.clean(0) == 1 and s.source(0) is None


def test_unknown_stages_are_reported():
    records = [{"stage": "N2"}, {"stage": "Bogus"}, {"stage": "foo"}, {"stage": None}, {"stage": "Bogus"}]
    assert unknown_stages(records) == ["Bogus", "foo"]
    assert unknown_stages([{"stage": "REM"}, {"stage": None}]) == []


def test_from_records_with_unknown_stage_raises_unless_replaced():
    records = [{"stage": "N2", "source": "human"}, {"stage": "Bogus", "source": "x", "confidence": 0.5}]
    with pytest.raises(ValueError):
        Scoring.from_records(records, 30)
    s = Scoring.from_records(records, 30, replace_unknown=True)
    assert s.stages() == ["N2", None]
    assert (s.source(1), s.confidence(1)) == (None, None)


def test_unscored_epoch_with_source_and_confidence_round_trips_through_records():
    s = Scoring(2, 30)
    s.set(0, None, source="NIDRA (m) - artifact", confidence=0.9, channels=["C3"])
    s.set_clean(0, False)
    again = Scoring.from_records(s.to_records(), 30)
    assert again.stage(0) is None
    assert (again.source(0), again.confidence(0), again.channels(0), again.clean(0)) == (
        "NIDRA (m) - artifact", 0.9, ["C3"], 0)


def test_probabilities_are_per_epoch_dicts_written_only_when_present():
    s = Scoring(3, 30)
    s.set([0, 1], "N2", source="NIDRA", probabilities=[{"Wake": 0.1, "N2": 0.9}, {"Wake": 0.6, "N2": 0.4}])
    s.set(2, "N1", probabilities={"N1": 1.0})
    assert s.probabilities(0) == {"Wake": 0.1, "N2": 0.9} and s.probabilities(1)["Wake"] == 0.6
    assert s.probabilities(2) == {"N1": 1.0}
    records = s.to_records()
    assert records[0]["probabilities"] == {"Wake": 0.1, "N2": 0.9}
    assert list(records[0])[:9] == RECORD_KEYS
    s.set(0, "N2")
    assert s.probabilities(0) is None and "probabilities" not in s.to_records()[0]
    again = Scoring.from_records(records, 30)
    assert again.probabilities(1) == {"Wake": 0.6, "N2": 0.4}


def test_probabilities_wrong_length_sequence_rejected():
    with pytest.raises(ValueError):
        Scoring(2, 30).set([0, 1], "N2", probabilities=[{"N2": 1.0}])


def test_fit_copies_probabilities_of_kept_epochs_but_not_to_copied_epochs():
    s = Scoring(2, 30)
    s.set(1, "N2", probabilities={"N2": 1.0})
    f = s.fitted(3)
    assert f.probabilities(1) == {"N2": 1.0} and f.probabilities(2) is None


def _scoring():
    s = Scoring(3, 30)
    s.set(0, "Wake", source="human")
    s.set(1, "N1", source="YASA", confidence=0.7, channels=["C3"])
    s.set(2, "N2", source="GSSC", confidence=0.6, channels=["C4"])
    s.set_clean(2, False)
    return s


def test_fit_same_length_is_equal_copy():
    s = _scoring()
    f = s.fitted(3)
    assert f is not s and f.to_records() == s.to_records()


def test_fit_longer_by_one_drops_last_epoch():
    f = _scoring().fitted(2)
    assert len(f) == 2 and f.stages() == ["Wake", "N1"]


def test_fit_longer_by_many_truncates():
    f = _scoring().fitted(1)
    assert len(f) == 1 and f.stage(0) == "Wake" and f.source(0) == "human"


def test_fit_shorter_by_one_copies_last_epoch():
    f = _scoring().fitted(4)
    assert f.stages() == ["Wake", "N1", "N2", "N2"]
    assert (f.source(3), f.confidence(3)) == ("GSSC", 0.6)


def test_fit_shorter_by_many_copies_last_until_match():
    f = _scoring().fitted(6)
    assert len(f) == 6
    assert f.stages()[2:] == ["N2"] * 4
    assert all((f.source(i), f.confidence(i)) == ("GSSC", 0.6) for i in range(2, 6))


def test_copied_epoch_has_empty_channels_and_clean_flag():
    f = _scoring().fitted(4)
    assert f.channels(3) == [] and f.clean(3) == 1
    assert f.channels(2) == ["C4"] and f.clean(2) == 0


def test_fit_keeps_epoch_length_and_time_spans():
    f = Scoring(2, 20).fitted(3)
    assert f.time_span(2) == (40, 60)


def test_fit_copy_of_unscored_last_epoch_is_unscored_and_empty_scoring_fits():
    assert Scoring(2, 30).fitted(4).stages() == [None] * 4
    assert Scoring(0, 30).fitted(3).stages() == [None] * 3
    assert len(Scoring(3, 30).fitted(0)) == 0


def test_fit_does_not_modify_original():
    s = _scoring()
    before = s.to_records()
    s.fitted(5)
    s.fitted(1)
    assert s.to_records() == before
