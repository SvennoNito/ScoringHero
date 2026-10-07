import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("reportlab")
pytest.importorskip("edfio")

SCRIPT = Path(__file__).resolve().parents[1] / "export" / "generate_sleep_report.py"


@pytest.fixture(scope="module")
def report():
    spec = importlib.util.spec_from_file_location("generate_sleep_report", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _stats(report, digits):
    stages = [{"digit": d} for d in digits]
    opts = {"sleep_stats": True, "stage_distribution": True}
    return report.calculate_sleep_statistics(stages, 60, opts)


def test_inconclusive_is_neither_sleep_nor_wake_but_counts_in_total(report):
    # 2 wake, 2 N2, 2 inconclusive, 2 unscored -> scored = 6
    out = _stats(report, [1, 1, -2, -2, 2, 2, None, None])
    assert "Total Sleep Time (TST):        2.0 min" in out
    assert "Total Recording Time (TRT):    6.0 min" in out
    assert "Sleep Efficiency:              33.3%" in out
    assert "Wake:                          2.0 min (0.0 h) - 33.3%" in out
    assert "N2:                            2.0 min (0.0 h) - 33.3%" in out
