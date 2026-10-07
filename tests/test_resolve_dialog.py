"""Offscreen smoke run of the resolution dialogs: each box is clicked via a patched exec."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from scoring_model.formats import Loaded  # noqa: E402
from widgets.resolveDialog import resolve_loaded  # noqa: E402


@pytest.fixture
def boxes(monkeypatch):
    """Records each box (text, button labels) and clicks the button named in `click`."""
    QApplication.instance() or QApplication([])
    seen, click = [], {"label": None}

    def fake_exec(self):
        labels = [b.text() for b in self.buttons()]
        seen.append((self.text(), labels))
        target = [b for b in self.buttons() if b.text() == click["label"]]
        self._clicked = target[0] if target else None

    monkeypatch.setattr(QMessageBox, "exec", fake_exec)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self._clicked)
    return seen, click


def _loaded(n, unrecognised=()):
    return Loaded(stages=["N2"] * n, unrecognised=list(unrecognised))


@pytest.mark.parametrize(
    "n, unknown, click, expect_len, labels",
    [
        (10, (), None, 10, None),
        (11, (), "OK", 10, ["OK"]),
        (9, (), "OK", 10, ["OK"]),
        (13, (), "Truncate", 10, ["Truncate", "Cancel"]),
        (13, (), "Cancel", None, ["Truncate", "Cancel"]),
        (5, (), "Copy last epoch", 10, ["Copy last epoch", "Cancel"]),
        (5, (), "Cancel", None, ["Copy last epoch", "Cancel"]),
        (10, ("Bogus",), "Replace with unscored", 10, ["Replace with unscored", "Cancel"]),
        (10, ("Bogus",), "Cancel", None, ["Replace with unscored", "Cancel"]),
    ],
)
def test_each_case(boxes, n, unknown, click, expect_len, labels):
    seen, state = boxes
    state["label"] = click
    result = resolve_loaded(None, _loaded(n, unknown), 10, 30)
    assert (len(result) if result is not None else None) == expect_len
    assert [b for _, b in seen] == ([labels] if labels else [])


def test_notice_closed_without_button_still_resolves(boxes):
    _, state = boxes
    state["label"] = None
    assert len(resolve_loaded(None, _loaded(11), 10, 30)) == 10


def test_unknown_then_length_both_shown(boxes):
    seen, state = boxes
    state["label"] = "Replace with unscored"
    # the same button label cannot answer the length box: it is cancelled there
    assert resolve_loaded(None, _loaded(14, ["x"]), 10, 30) is None
    assert [b[0] for _, b in seen] == ["Replace with unscored", "Truncate"]
