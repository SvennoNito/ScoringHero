"""Tests for the format table: loaders and writers on temporary files. No Qt."""

import json

import pytest

from scoring_model.formats import FORMATS, to_scoring
from scoring_model.scoring import Scoring

STAGES = ["Wake", "N1", "N2", "N3", "REM", "N2"]


def scoring_of(stages, epoch_length_s=30, confidence=0.8):
    s = Scoring(len(stages), epoch_length_s)
    for i, stage in enumerate(stages):
        if stage is not None:  # unscored carries nothing unless passed explicitly
            s.set(i, stage, "human", confidence, ["C3"])
    return s


def load(name, path):
    return FORMATS[name].loader(str(path))


def test_table_lists_every_format_with_label_and_filter():
    assert list(FORMATS) == ["scoringhero", "vis", "yasa", "sleeptrip", "sleepyland", "gssc"]
    assert FORMATS["vis"].file_filter == "*.vis"
    assert FORMATS["sleepyland"].file_filter == "*.annot"
    assert all(f.label and callable(f.loader) and callable(f.writer) for f in FORMATS.values())


# ---- fixtures per format ---------------------------------------------------------


def test_vis_fixture(tmp_path):
    p = tmp_path / "a.vis"
    p.write_text("0\n1 0\n2 1 comment\n3 2\n4 3\n5 r\n6 e\n")
    loaded = load("vis", p)
    assert loaded.stages == ["Wake", "N1", "N2", "N3", "REM", "REM"]
    assert loaded.unrecognised == []


def test_vis_fills_missing_epochs_and_reports_bad_rows(tmp_path):
    p = tmp_path / "a.vis"
    p.write_text("0\n1 0\n3 2\n4 x\nbad\n5 r\n")
    loaded = load("vis", p)
    assert loaded.stages == ["Wake", "Wake", "N2", None, "REM"]
    assert loaded.unrecognised == ["bad", "x"]


def test_yasa_fixture_skips_non_matching_rows(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("header\nW\nn1\nNREM2\n\n3\nREM\nbogus\n4\n")
    assert load("yasa", p).stages == ["Wake", "N1", "N2", "N3", "REM", "REM"]


def test_sleeptrip_fixture_skips_rows_and_returns_artefact_column(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("stage,art\n0,0\n1,1\n2\n3,0\n5,0\n4,0\n")
    loaded = load("sleeptrip", p)
    assert loaded.stages == ["Wake", "N1", "N2", "N3", "REM"]
    assert loaded.source == ["Sleeptrip"] * 5
    assert loaded.annotations == [0, 0, 1, 0, 0, 0, 0]


def test_sleepyland_fixture_with_confidence(tmp_path):
    p = tmp_path / "a.annot"
    p.write_text(
        "Epoch\tStage\tStart\tEnd\tDuration\tMeta\n"
        "1\tW\t0\t30\t30\tpW=0.9; pN1=0.1; pN2=0; pN3=0; pR=0\n"
        "2\tR\t30\t60\t30\tpW=0; pN1=0; pN2=0; pN3=0; pR=0.6\n"
    )
    loaded = load("sleepyland", p)
    assert loaded.stages == ["Wake", "REM"]
    assert loaded.confidence == [0.9, 0.6]
    assert loaded.source == ["Sleepyland"] * 2


def test_sleepyland_reports_unknown_stage_and_short_row(tmp_path):
    p = tmp_path / "a.annot"
    p.write_text(
        "Epoch\tStage\tStart\tEnd\tDuration\tMeta\n"
        "1\tX\t0\t30\t30\tpW=1\n"
        "2\tN2\t30\t60\t30\tpN2=0.5\n"
        "3\tW\n"
    )
    loaded = load("sleepyland", p)
    assert loaded.stages == [None, "N2", None]
    assert loaded.confidence == [None, 0.5, None]
    assert loaded.source == [None, "Sleepyland", None]
    assert loaded.unrecognised == ["X", "3\tW"]


def test_gssc_fixture_with_confidence(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text(
        "Epoch,Start,Stage,pWake,pN1,pN2,pN3,pREM\n"
        "1,0,0,0.7,0.1,0.1,0.05,0.05\n"
        "2,30,4,0,0,0,0.2,0.8\n"
    )
    loaded = load("gssc", p)
    assert loaded.stages == ["Wake", "REM"]
    assert loaded.confidence == [0.7, 0.8]
    assert loaded.source == ["GSSC"] * 2


def test_gssc_reports_unknown_code(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("Epoch,Start,Stage,pWake,pN1,pN2,pN3,pREM\n1,0,9,1,0,0,0,0\n2,30,2,0,0,0.5,0,0\n")
    loaded = load("gssc", p)
    assert loaded.stages == [None, "N2"]
    assert loaded.unrecognised == ["1,0,9,1,0,0,0,0"]


def test_scoringhero_loads_stage_name_over_contradicting_digit(tmp_path):
    p = tmp_path / "a.json"
    records = [
        {"epoch": 1, "stage": "N2", "digit": 1, "confidence": 0.3, "channels": ["C3"], "clean": 0, "source": "GSSC"},
        {"epoch": 2, "stage": None, "digit": None},
    ]
    p.write_text(json.dumps([records, [{"key": "A", "epoch": 1}]]))
    loaded = load("scoringhero", p)
    assert loaded.stages == ["N2", None]
    assert loaded.annotations == [{"key": "A", "epoch": 1}]
    s = to_scoring(loaded, 30)
    assert s.digit(0) == -2
    assert (s.source(0), s.confidence(0), s.channels(0), s.clean(0)) == ("GSSC", 0.3, ["C3"], 0)
    assert s.stage(1) is None and s.clean(1) == 1


def test_scoringhero_reports_unknown_stages(tmp_path):
    p = tmp_path / "a.json"
    p.write_text(json.dumps([[{"stage": "Bogus"}, {"stage": "Wake"}, {"stage": "Foo"}], []]))
    loaded = load("scoringhero", p)
    assert loaded.stages == [None, "Wake", None]
    assert loaded.unrecognised == ["Bogus", "Foo"]


def test_loader_raises_on_missing_file(tmp_path):
    for f in FORMATS.values():
        with pytest.raises(OSError):
            f.loader(str(tmp_path / "missing"))


# ---- writers ---------------------------------------------------------------------


@pytest.mark.parametrize("name", list(FORMATS))
def test_writer_round_trips_through_loader(tmp_path, name):
    p = tmp_path / "out"
    FORMATS[name].writer(scoring_of(STAGES), str(p))
    assert load(name, p).stages == STAGES


def test_round_trip_keeps_confidence_where_format_has_it(tmp_path):
    for name in ("sleepyland", "gssc", "scoringhero"):
        p = tmp_path / name
        FORMATS[name].writer(scoring_of(STAGES), str(p))
        assert load(name, p).confidence == [0.8] * len(STAGES)


def test_sleeptrip_round_trips_artefact_flag(tmp_path):
    s = scoring_of(STAGES)
    s.set_clean(2, 0)
    p = tmp_path / "a.csv"
    FORMATS["sleeptrip"].writer(s, str(p))
    assert load("sleeptrip", p).annotations == [0, 0, 1, 0, 0, 0]


def test_scoringhero_writer_writes_records_and_given_events(tmp_path):
    s = scoring_of(STAGES)
    p = tmp_path / "a.json"
    FORMATS["scoringhero"].writer(s, str(p), events=[{"key": "A"}])
    records, events = json.loads(p.read_text())
    assert records == s.to_records()
    assert events == [{"key": "A"}]
    assert to_scoring(load("scoringhero", p), 30).to_records() == s.to_records()


def test_writers_keep_exact_on_disk_output(tmp_path):
    s = scoring_of(["Wake", "REM", None])
    s.set(1, "REM", "human", None)

    def text(name, suffix):
        p = tmp_path / f"o{suffix}"
        FORMATS[name].writer(s, str(p))
        return p.read_bytes().decode().replace("\r\n", "\n")

    assert text("vis", ".vis") == "0\n1 0\n2 r\n3 0\n"
    assert text("yasa", ".txt") == "W\nR\n\n"
    assert text("sleeptrip", ".csv") == "0,0\n5,0\n,0\n"
    assert text("sleepyland", ".annot") == (
        "Epoch\tStage\tStart\tEnd\tDuration\tMeta\n"
        "1\tW\t0\t30\t30\tpW=0.8; pN1=0.0; pN2=0.0; pN3=0.0; pR=0.0\n"
        "2\tR\t30\t60\t30\tpW=0.0; pN1=0.0; pN2=0.0; pN3=0.0; pR=1.0\n"
        "3\tW\t60\t90\t30\tpW=0.0; pN1=0.0; pN2=0.0; pN3=0.0; pR=0.0\n"
    )
    assert text("gssc", ".csv").splitlines()[1:] == [
        "1,0,0,0.8,0.0,0.0,0.0,0.0",
        "2,30,4,0.0,0.0,0.0,0.0,1.0",
        "3,60,0,1.0,0.0,0.0,0.0,0.0",
    ]
