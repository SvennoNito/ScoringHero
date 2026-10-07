"""Length/unknown-stage resolution: pure decision logic, no dialogs."""

import pytest

from scoring_model.formats import Loaded
from scoring_model.resolve import diagnose, resolve


def _loaded(n, unrecognised=()):
    stages = ["N2"] * n
    stages[-1] = "REM"
    return Loaded.from_columns(
        stages,
        "gssc",
        [0.9] * (n - 1) + [0.4],
        unrecognised=list(unrecognised),
    )


@pytest.mark.parametrize(
    "loaded_n, recording_n, kind, choices",
    [
        (10, 10, "exact", ()),
        (11, 10, "longer_1", ("ok",)),
        (13, 10, "longer_n", ("truncate",)),
        (9, 10, "shorter_1", ("ok",)),
        (5, 10, "shorter_n", ("copy_last",)),
    ],
)
def test_length_case_and_choices(loaded_n, recording_n, kind, choices):
    p = diagnose(_loaded(loaded_n), recording_n)
    assert (p.length_kind, p.length_choices) == (kind, choices)
    assert p.unknown == ()


def test_unknown_stages_are_listed_with_replace_choice():
    p = diagnose(_loaded(10, ["Bogus", "foo"]), 10)
    assert p.unknown == ("Bogus", "foo")
    assert p.unknown_choices == ("replace",)
    assert diagnose(_loaded(10), 10).unknown_choices == ()


def _always(choice):
    return lambda question: choice


def test_exact_needs_no_question():
    def ask(question):
        raise AssertionError("no question expected")

    s = resolve(_loaded(10), 10, 30, ask)
    assert len(s) == 10 and s.stage(9) == "REM" and s.epoch_length_s == 30


def test_longer_by_one_drops_last_epoch_after_notice():
    asked = []

    def ask(q):
        asked.append(q)
        return "ok"

    s = resolve(_loaded(11), 10, 30, ask)
    assert len(s) == 10 and s.stage(9) == "N2"
    assert [q.topic for q in asked] == ["length"] and asked[0].kind == "longer_1"


def test_longer_by_many_truncates():
    s = resolve(_loaded(14), 10, 30, _always("truncate"))
    assert len(s) == 10 and s.stages()[:9] == ["N2"] * 9


def test_shorter_by_one_copies_last_epoch_with_stage_source_confidence():
    s = resolve(_loaded(9), 10, 30, _always("ok"))
    assert len(s) == 10
    assert (s.stage(9), s.source(9), s.confidence(9)) == ("REM", "gssc", 0.4)


def test_shorter_by_many_copies_last_epoch_until_match():
    s = resolve(_loaded(6), 10, 30, _always("copy_last"))
    assert s.stages() == ["N2"] * 5 + ["REM"] * 5
    assert all(s.confidence(i) == 0.4 for i in range(5, 10))


def test_unknown_stages_replaced_with_unscored():
    loaded = _loaded(10, ["Bogus"])
    loaded.records[3]["stage"] = "Bogus"
    s = resolve(loaded, 10, 30, _always("replace"))
    assert s.stage(3) is None and s.source(3) is None


@pytest.mark.parametrize("n", [10, 14, 6])
def test_cancel_is_reported_as_none(n):
    assert resolve(_loaded(n, ["x"]), 10, 30, _always(None)) is None


def test_unknown_asked_before_length_and_cancel_on_length_stops():
    asked = []

    def ask(q):
        asked.append(q.topic)
        return "replace" if q.topic == "unknown" else None

    assert resolve(_loaded(14, ["x"]), 10, 30, ask) is None
    assert asked == ["unknown", "length"]


def test_both_problems_resolved():
    def ask(q):
        return "replace" if q.topic == "unknown" else "truncate"

    s = resolve(_loaded(14, ["x"]), 10, 30, ask)
    assert len(s) == 10
