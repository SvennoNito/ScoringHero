"""Channel settings: the single declaration of every per-channel setting.

Each channel of a recording is a plain dict holding every setting declared in
_SETTINGS, its "Signal_index" (position of its file signal in the loaded data;
extra files appended in load order), plus the markers "derived"/"source_channel"
on a derived channel. Channel names are unique within a recording.
"Ordinary" channels below are the non-derived ones (a signal from the file).
No file, GUI or application-state access here.
"""

from collections import namedtuple

from eeg.units import is_voltage_unit, normalize_unit

# Whether a setting determines the channel's displayed signal
DISPLAY = "display"  # no: only how it is drawn
REBUILD = "rebuild"  # yes (re-reference -> filter -> flip)

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


# name: (default for a _Signal, DISPLAY or REBUILD)
_SETTINGS = {
    "Channel_name":         (lambda s: s.name, DISPLAY),
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
    return {**{name: default(signal) for name, (default, _) in _SETTINGS.items()}, "Signal_index": signal.index}


def _free_name(base, taken):
    """base followed by the fewest '*' (at least one) not among the taken names."""
    name = base + "*"
    while name in taken:
        name += "*"
    return name


def _make_names_unique(channels):
    """Rename later channels sharing an earlier channel's name to <name>*, <name>**, ...
    (first free), in place; references to that name keep meaning the first one."""
    taken = {c["Channel_name"] for c in channels}
    seen = set()
    for channel in channels:
        if channel["Channel_name"] in seen:
            channel["Channel_name"] = _free_name(channel["Channel_name"], taken)
            taken.add(channel["Channel_name"])
        seen.add(channel["Channel_name"])
    return channels


def default_channels(number_of_signals, channel_names, units=None):
    """Channel settings for a newly opened recording, one per signal in the file.
    units: per-signal unit strings; None or a missing entry means unknown.
    Signals sharing a name get unique names (<name>*, ...)."""
    return _make_names_unique([
        _default_channel(_Signal(
            i,
            channel_names[i] if i < len(channel_names) else f"Channel {i + 1}",
            units[i] if units is not None and i < len(units) else None,
            number_of_signals,
        ))
        for i in range(number_of_signals)
    ])


def _is_derived(channel):
    return channel.get("derived", False)


def _completed(channel, base):
    """channel with every setting it lacks taken from base; stored values win."""
    return {**{name: base[name] for name in _SETTINGS}, **channel}


def _complete_derived(derived, ordinary, number_of_signals):
    """Fill the derived channels' missing settings and file signal from their source
    channel among the (completed) ordinary channels; without one, from an unknown
    signal's defaults."""
    by_name = {}
    for channel in ordinary:
        by_name.setdefault(channel["Channel_name"], channel)
    result = []
    for channel in derived:
        source = by_name.get(channel.get("source_channel"))
        if source is None:
            source = _default_channel(_Signal(0, channel["Channel_name"], None, number_of_signals))
        result.append({"Signal_index": source["Signal_index"], **_completed(channel, source)})
    return result


def _file_signal_indices(stored, defaults):
    """File signal of each stored ordinary channel lacking a Signal_index: by name if
    every channel name matches a distinct file signal name, otherwise by position."""
    names = [c["Channel_name"] for c in stored]
    by_file_name = {d["Channel_name"]: d["Signal_index"] for d in defaults}
    if len(stored) == len(defaults) and len(set(names)) == len(names) and all(n in by_file_name for n in names):
        return [by_file_name[n] for n in names]
    return list(range(len(stored)))


def complete_channels(channels, number_of_signals, channel_names, units=None):
    """Channel list loaded from a (possibly older) configuration file, completed:
    ordinary channels get missing settings from their defaults, derived channels
    from their source channel. Stored values and positions are kept. Ordinary
    channels are truncated or padded with defaults (appended) to
    number_of_signals. A channel sharing an earlier one's name is renamed
    <name>*, ..., ordinary channels taking precedence, so references to that name
    keep meaning the first ordinary channel."""
    defaults = default_channels(number_of_signals, channel_names, units)
    stored = [c for c in channels if not _is_derived(c)][:number_of_signals]
    indices = _file_signal_indices(stored, defaults)
    ordinary = [{"Signal_index": i, **_completed(c, d)} for c, d, i in zip(stored, defaults, indices)]
    ordinary += defaults[len(ordinary):]
    derived = _complete_derived([c for c in channels if _is_derived(c)], ordinary, number_of_signals)
    _make_names_unique(ordinary + derived)

    # Back to the stored order (truncated ordinary channels dropped), padding last
    kept = {id(c) for c in stored}
    next_ordinary, next_derived = iter(ordinary), iter(derived)
    result = [next(next_derived) if _is_derived(c) else next(next_ordinary)
              for c in channels if _is_derived(c) or id(c) in kept]
    return result + list(next_ordinary)


def merge_template(channels, template):
    """Merge a saved channel template into freshly built default channels.

    An ordinary channel whose name matches a template entry takes that entry's
    settings (defaults underneath for settings saved before they existed) but
    keeps its own file signal. A derived template channel is recreated when its
    source channel is present, with missing settings and the file signal taken
    from that source."""
    template = [{k: v for k, v in entry.items() if k != "Signal_index"} for entry in template]
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
    return _make_names_unique(ordinary + _complete_derived(derived, ordinary, len(channels)))


def derive_channel(channels, source_name, reference_name):
    """New derived channel source − reference: the source channel's settings and
    file signal, re-referenced to reference_name, shown, marked as derived from
    the source and named <source>* (first free of *, **, ...)."""
    source = next(c for c in channels if c["Channel_name"] == source_name)
    return {
        **source,
        "Channel_name": _free_name(source_name, {c["Channel_name"] for c in channels}),
        "Re_reference": reference_name,
        "Display_on_screen": 1,
        "derived": True,
        "source_channel": source_name,
    }


# General settings holding the name of the channel an analysis panel shows
ANALYSIS_CHANNEL_KEYS = ("Channel_for_spectogram", "Wavelet_channel", "Periodogram_channel")


def rename_channel(channels, general, old_name, new_name):
    """Rename channel old_name to new_name in place, re-pointing every reference to
    it: other channels' Re_reference, derived channels' source_channel and the
    analysis channel selectors in general. Raises ValueError (changing nothing) if
    another channel already has new_name."""
    if new_name == old_name:
        return
    if any(c["Channel_name"] == new_name for c in channels):
        raise ValueError(f"Channel name already used: {new_name}")
    for channel in channels:
        for key in ("Channel_name", "Re_reference", "source_channel"):
            if channel.get(key) == old_name:
                channel[key] = new_name
    for key in ANALYSIS_CHANNEL_KEYS:
        if general.get(key) == old_name:
            general[key] = new_name


_REBUILD_SETTINGS = [name for name, (_, effect) in _SETTINGS.items() if effect == REBUILD]


def displayed_signal_inputs(channels):
    """Per channel name, everything its displayed signal depends on, free of channel
    names: its file signal, its reference's file signal (None if not re-referenced)
    and its other signal-affecting settings. Renames and moves leave these equal."""
    signal_index = {c["Channel_name"]: c["Signal_index"] for c in channels}
    return {
        c["Channel_name"]: (
            c["Signal_index"],
            signal_index.get(c["Re_reference"]),
            tuple(c[name] for name in _REBUILD_SETTINGS if name != "Re_reference"),
        )
        for c in channels
    }


def rebuild_fingerprint(channels):
    """Values of every signal-affecting setting of every channel; equal
    fingerprints mean the displayed signal is unchanged."""
    return tuple(tuple(channel[name] for name in _REBUILD_SETTINGS) for channel in channels)
