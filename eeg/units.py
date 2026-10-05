# Voltage unit (normalized spelling) -> factor to microvolts
TO_UV = {"V": 1e6, "mV": 1e3, "uV": 1.0}
_VOLTAGE_UNITS_LOWER = {u.lower() for u in TO_UV}


def normalize_unit(unit):
    """'µV'/'μV' -> 'uV'; None or blank -> None (unknown)."""
    if unit is None:
        return None
    unit = str(unit).strip().replace("\u00b5", "u").replace("\u03bc", "u")
    return unit or None


def is_voltage_unit(unit):
    """True for V, mV, uV in any case or micro-sign spelling; False for other or unknown units."""
    unit = normalize_unit(unit)
    return unit is not None and unit.lower() in _VOLTAGE_UNITS_LOWER
