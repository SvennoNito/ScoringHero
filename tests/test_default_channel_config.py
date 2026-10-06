"""
Tests for unit classification and selecting a channel by vertical position.
Channel settings defaults, completion and template merge: test_channel_settings.py.
"""

from config.default_config import default_configuration


def test_is_voltage_unit():
    """Voltage units in any case and micro sign; non-voltage and unknown are not."""
    from eeg.units import is_voltage_unit
    for unit in ["V", "mV", "uV", "µV", "μV", "UV", " mv "]:
        assert is_voltage_unit(unit), unit
    for unit in ["g", "m/s2", "%", "", None]:
        assert not is_voltage_unit(unit), unit
    print("[OK] is_voltage_unit")


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
    test_is_voltage_unit()
    test_channel_from_selection_negative_shift()
