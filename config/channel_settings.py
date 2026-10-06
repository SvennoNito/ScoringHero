"""Channel settings: the single declaration of every per-channel setting.

Each channel of a recording is a plain dict holding every setting declared in
_SETTINGS, plus the markers "derived"/"source_channel" on a derived channel.
"Ordinary" channels below are the non-derived ones (a signal from the file).
No file, GUI or application-state access here.
"""

from collections import namedtuple

from eeg.units import is_voltage_unit, normalize_unit

# Effect of changing a setting
DISPLAY = "display"  # redraw only
REBUILD = "rebuild"  # recompute the displayed signal (re-reference -> filter -> flip)
RENAME = "rename"    # handled by the rename path

# Signal a default is computed for: position in the file, name, unit, signal count
_Signal = namedtuple("_Signal", "index name unit count")


def _scaling(count):
    if count <= 3:
        return 50
    if count <= 7:
        return 75
    return 100


def _color(name):
    upper = name.upper()
    if "EOG" in upper:
        return "Blue"
    if "ECG" in upper:
        return "Magenta"
    if "EMG" in upper:
        return "Orange"
    return "Black"


def _shown(index, count):
    if count == 9 and index in (1, 3, 5):
        return 0
    return 1 if index < 9 else 0


def _subtract_median(unit):
    """On for a known non-voltage unit (e.g. 'g'); off for voltage or unknown."""
    return normalize_unit(unit) is not None and not is_voltage_unit(unit)


# name: (default for a _Signal, effect when changed)
_SETTINGS = {
    "Channel_name":         (lambda s: s.name, RENAME),
    "Channel_color":        (lambda s: _color(s.name), DISPLAY),
    "Display_on_screen":    (lambda s: _shown(s.index, s.count), DISPLAY),
    "Scaling_factor":       (lambda s: _scaling(s.count), DISPLAY),
    "Vertical_shift":       (lambda s: 0, DISPLAY),
    "Re_reference":         (lambda s: "None", REBUILD),
    "Flip_polarity":        (lambda s: False, REBUILD),
    "Subtract_median":      (lambda s: _subtract_median(s.unit), DISPLAY),
    "Line_width":           (lambda s: 2.0, DISPLAY),
    "Filter_hp_enabled":    (lambda s: False, REBUILD),
    "Filter_hp_cutoff":     (lambda s: 0.3, REBUILD),
    "Filter_hp_order":      (lambda s: 4, REBUILD),
    "Filter_lp_enabled":    (lambda s: False, REBUILD),
    "Filter_lp_cutoff":     (lambda s: 50.0, REBUILD),
    "Filter_lp_order":      (lambda s: 4, REBUILD),
    "Filter_notch_enabled": (lambda s: False, REBUILD),
    "Filter_notch_cutoff":  (lambda s: 50.0, REBUILD),
    "Filter_notch_order":   (lambda s: 4, REBUILD),
}


def _default_channel(signal):
    return {name: default(signal) for name, (default, _) in _SETTINGS.items()}


def default_channels(number_of_signals, channel_names, units=None):
    """Channel settings for a newly opened recording, one per signal in the file.
    units: per-signal unit strings; None or a missing entry means unknown."""
    return [
        _default_channel(_Signal(
            i,
            channel_names[i] if i < len(channel_names) else f"Channel {i + 1}",
            units[i] if units is not None and i < len(units) else None,
            number_of_signals,
        ))
        for i in range(number_of_signals)
    ]


def _is_derived(channel):
    return channel.get("derived", False)


def _completed(channel, base):
    """channel with every setting it lacks taken from base; stored values win."""
    return {**{name: base[name] for name in _SETTINGS}, **channel}


def _complete_derived(derived, ordinary, number_of_signals):
    """Fill the derived channels' missing settings from their source channel among
    the (completed) ordinary channels; without one, from an unknown signal's defaults."""
    by_name = {}
    for channel in ordinary:
        by_name.setdefault(channel["Channel_name"], channel)
    result = []
    for channel in derived:
        source = by_name.get(channel.get("source_channel"))
        if source is None:
            source = _default_channel(_Signal(0, channel["Channel_name"], None, number_of_signals))
        result.append(_completed(channel, source))
    return result


def complete_channels(channels, number_of_signals, channel_names, units=None):
    """Channel list loaded from a (possibly older) configuration file, completed:
    ordinary channels get missing settings from their defaults, derived channels
    from their source channel. Stored values are never overwritten. Ordinary
    channels are truncated or padded with defaults to number_of_signals; derived
    channels follow them."""
    defaults = default_channels(number_of_signals, channel_names, units)
    ordinary = [c for c in channels if not _is_derived(c)][:number_of_signals]
    ordinary = [_completed(c, d) for c, d in zip(ordinary, defaults)] + defaults[len(ordinary):]
    derived = [c for c in channels if _is_derived(c)]
    return ordinary + _complete_derived(derived, ordinary, number_of_signals)


def merge_template(channels, template):
    """Merge a saved channel template into freshly built default channels.

    An ordinary channel whose name matches a template entry takes that entry's
    settings (defaults underneath for settings saved before they existed). A
    derived template channel is recreated when its source channel is present,
    with missing settings completed from that source."""
    by_name = {}
    for entry in template:
        by_name.setdefault(entry.get("Channel_name"), entry)

    ordinary = []
    for channel in channels:
        saved = by_name.get(channel["Channel_name"])
        if saved and not _is_derived(saved):
            channel = {**channel, **saved}
        ordinary.append(channel)

    names = {c["Channel_name"] for c in ordinary}
    derived = [e for e in template if _is_derived(e) and e.get("source_channel") in names]
    return ordinary + _complete_derived(derived, ordinary, len(channels))


def derive_channel(source, reference_name):
    """New derived channel source − reference: the source channel's settings,
    re-referenced to reference_name, shown, and marked as derived from source.
    Its name starts as the source channel's name."""
    return {
        **source,
        "Re_reference": reference_name,
        "Display_on_screen": 1,
        "derived": True,
        "source_channel": source["Channel_name"],
    }


def setting_effect(name):
    """DISPLAY, REBUILD or RENAME: what changing setting `name` requires."""
    return _SETTINGS[name][1]


_REBUILD_SETTINGS = [name for name, (_, effect) in _SETTINGS.items() if effect == REBUILD]


def rebuild_fingerprint(channels):
    """Values of every signal-affecting setting of every channel; equal
    fingerprints mean the displayed signal is unchanged."""
    return tuple(tuple(channel[name] for name in _REBUILD_SETTINGS) for channel in channels)
