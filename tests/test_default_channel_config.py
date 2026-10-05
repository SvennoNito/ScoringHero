"""
Tests for default channel configuration: scaling by number of signals,
subtract-median by unit, and channel-template override.
"""

from config.default_config import default_configuration
from config.channel_template import apply_channel_template
from config.check_for_compatability import check_for_compatability
import os
import tempfile


def _scales(n, units=None):
    names = [f"Ch{i + 1}" for i in range(n)]
    config = default_configuration(n, 100, names, units)
    return [c["Scaling_factor"] for c in config[1]]


def test_default_scaling_by_signal_count():
    """50 for <=3 signals, 75 for 4-7, 100 for >=8."""
    expected = {1: 50, 2: 50, 3: 50, 4: 75, 5: 75, 7: 75, 8: 100, 9: 100, 12: 100}
    for n, scale in expected.items():
        scales = _scales(n)
        assert len(scales) == n
        assert all(s == scale for s in scales), f"n={n}: {scales}"
    print("[OK] default scaling 50/75/100 at boundaries 3/4/7/8")


def test_units_none_and_given():
    """Units unknown (None) or given does not break the default configuration."""
    assert _scales(4, None) == _scales(4, ["uV"] * 4)
    print("[OK] units parameter accepted")


def test_channel_template_overrides_scaling():
    """A channel template entry for the channel name overrides the default."""
    names = ["C3", "C4", "EOG"]
    config = default_configuration(3, 100, names, None)
    template = [dict(config[1][0], Channel_name="C3", Scaling_factor=200)]
    config = apply_channel_template(config, template, names)
    assert config[1][0]["Scaling_factor"] == 200
    assert config[1][1]["Scaling_factor"] == 50
    assert config[1][2]["Scaling_factor"] == 50
    print("[OK] channel template overrides default scaling")


def _submed(units):
    names = [f"Ch{i + 1}" for i in range(len(units))]
    config = default_configuration(len(units), 100, names, units)
    return [c["Subtract_median"] for c in config[1]]


def test_subtract_median_default_by_unit():
    """On for non-voltage units, off for voltage and unknown."""
    assert _submed(["uV", "mV", "V", "µV", "UV", "g", "m/s2"]) == [False] * 5 + [True] * 2
    assert _submed([None, ""]) == [False, False]
    names = ["A", "B"]
    config = default_configuration(2, 100, names, None)
    assert [c["Subtract_median"] for c in config[1]] == [False, False]
    print("[OK] subtract median default by unit")


def test_channel_template_overrides_subtract_median():
    names = ["EEG", "ACC"]
    config = default_configuration(2, 100, names, ["uV", "g"])
    template = [
        dict(config[1][0], Channel_name="EEG", Subtract_median=True),
        dict(config[1][1], Channel_name="ACC", Subtract_median=False),
    ]
    config = apply_channel_template(config, template, names)
    assert config[1][0]["Subtract_median"] is True
    assert config[1][1]["Subtract_median"] is False
    # Old template without the key keeps the default
    config = default_configuration(2, 100, names, ["uV", "g"])
    old = [{k: v for k, v in config[1][1].items() if k != "Subtract_median"}]
    config = apply_channel_template(config, old, names)
    assert config[1][1]["Subtract_median"] is True
    print("[OK] channel template overrides subtract median")


def test_compatibility_filler_adds_subtract_median():
    names = ["EEG", "ACC"]
    units = ["uV", "g"]
    config = default_configuration(2, 100, names, units)
    for c in config[1]:
        del c["Subtract_median"]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "x.config.json")
        config = check_for_compatability(config, path, 2, 100, names, units)
    assert [c["Subtract_median"] for c in config[1]] == [False, True]
    print("[OK] compatibility filler adds subtract median")


def test_compatibility_filler_derived_channel_gets_neutral_subtract_median():
    """A legacy derived channel has no unit of its own: it must not inherit the
    unit-based default of the first signal (here a non-voltage one)."""
    names = ["ACC", "EEG"]
    units = ["g", "uV"]
    config = default_configuration(2, 100, names, units)
    derived = {k: v for k, v in config[1][1].items() if k != "Subtract_median"}
    derived["derived"] = True
    config[1].append(derived)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "x.config.json")
        config = check_for_compatability(config, path, 2, 100, names, units)
    assert config[1][0]["Subtract_median"] is True
    assert config[1][2]["Subtract_median"] is False
    print("[OK] compatibility filler gives derived channel neutral subtract median")


def test_is_voltage_unit():
    """Voltage units in any case and micro sign; non-voltage and unknown are not."""
    from eeg.units import is_voltage_unit
    for unit in ["V", "mV", "uV", "µV", "μV", "UV", " mv "]:
        assert is_voltage_unit(unit), unit
    for unit in ["g", "m/s2", "%", "", None]:
        assert not is_voltage_unit(unit), unit
    print("[OK] is_voltage_unit")


def test_line_width_default_template_and_filler():
    names = ["EEG", "ACC"]
    config = default_configuration(2, 100, names, None)
    assert [c["Line_width"] for c in config[1]] == [1.0, 1.0]
    template = [dict(config[1][0], Channel_name="EEG", Line_width=3.5)]
    config = apply_channel_template(config, template, names)
    assert config[1][0]["Line_width"] == 3.5
    assert config[1][1]["Line_width"] == 1.0
    # Older configuration without the key gets 1.0
    config = default_configuration(2, 100, names, None)
    for c in config[1]:
        del c["Line_width"]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "x.config.json")
        config = check_for_compatability(config, path, 2, 100, names, None)
    assert [c["Line_width"] for c in config[1]] == [1.0, 1.0]
    print("[OK] line width default, template, compatibility filler")


class _P:
    def __init__(self, y):
        self._y = y

    def y(self):
        return self._y


def test_channel_from_selection_negative_shift():
    from signal_processing.channel_from_selection import channel_from_selection

    names = ["A", "B", "C"]
    config = default_configuration(3, 100, names, None)
    config[0]["Distance_between_channels_muV"] = 100
    config[1][1]["Display_on_screen"] = False  # hidden channel in the middle
    config[1][2]["Vertical_shift"] = -50
    # Visible: A (anchor 0), C (anchor -50 - 100*2*1 = -250)
    for y, expected in [(10, 0), (-60, 0), (-240, 2), (-300, 2)]:
        _, channel = channel_from_selection(config, [_P(y), _P(y)], [0, 0])
        assert channel == expected, (y, channel)
    print("[OK] channel_from_selection with negative shift")


if __name__ == "__main__":
    test_default_scaling_by_signal_count()
    test_units_none_and_given()
    test_channel_template_overrides_scaling()
    test_subtract_median_default_by_unit()
    test_channel_template_overrides_subtract_median()
    test_compatibility_filler_adds_subtract_median()
    test_compatibility_filler_derived_channel_gets_neutral_subtract_median()
    test_is_voltage_unit()
    test_line_width_default_template_and_filler()
    test_channel_from_selection_negative_shift()
