"""Tests for the channel settings module: defaults, completion of older files,
channel template merge, derived channels, renaming and the rebuild fingerprint."""

import pytest

from config.channel_settings import (
    complete_channels,
    default_channels,
    derive_channel,
    merge_template,
    rebuild_fingerprint,
    rename_channel,
)


def _names(n):
    return [f"Ch{i + 1}" for i in range(n)]


def test_default_scaling_by_signal_count():
    """50 for <=3 signals, 75 for 4-7, 100 for >=8."""
    for n, expected in [(1, 50), (3, 50), (4, 75), (7, 75), (8, 100), (12, 100)]:
        scales = [c["Scaling_factor"] for c in default_channels(n, _names(n))]
        assert scales == [expected] * n, (n, scales)


def test_subtract_median_default_by_unit():
    """On for non-voltage units, off for voltage and unknown."""
    units = ["uV", "g", "m/s2", "mV", "V", ""]
    channels = default_channels(len(units), _names(len(units)), units)
    assert [c["Subtract_median"] for c in channels] == [False, True, True, False, False, False]
    assert [c["Subtract_median"] for c in default_channels(2, ["A", "B"])] == [False, False]


def test_default_line_width():
    assert [c["Line_width"] for c in default_channels(2, ["EEG", "ACC"])] == [2.0, 2.0]


def test_default_colour_by_channel_type():
    channels = default_channels(4, ["C3", "EOG L", "ecg", "Chin EMG"])
    assert [c["Channel_color"] for c in channels] == ["Black", "Blue", "Magenta", "Orange"]


def test_nine_signals_hide_second_fourth_sixth():
    shown = [bool(c["Display_on_screen"]) for c in default_channels(9, _names(9))]
    assert shown == [True, False, True, False, True, False, True, True, True]


def test_default_channels_named_and_unfiltered():
    channels = default_channels(2, ["C3", "C4"])
    assert [c["Channel_name"] for c in channels] == ["C3", "C4"]
    for c in channels:
        assert c["Re_reference"] == "None"
        assert not c["Filter_hp_enabled"] and not c["Filter_lp_enabled"] and not c["Filter_notch_enabled"]


def test_file_signals_with_the_same_name_get_unique_names():
    channels = default_channels(4, ["EMG", "EMG", "C3", "EMG"])
    assert [c["Channel_name"] for c in channels] == ["EMG", "EMG*", "C3", "EMG**"]
    assert [c["Signal_index"] for c in channels] == [0, 1, 2, 3]


def _without(channel, *names):
    return {k: v for k, v in channel.items() if k not in names}


def test_complete_fills_missing_without_overwriting():
    names, units = ["EEG", "ACC"], ["uV", "g"]
    saved = default_channels(2, names, units)
    saved[0]["Scaling_factor"] = 321
    saved = [_without(c, "Subtract_median", "Line_width") for c in saved]
    channels = complete_channels(saved, 2, names, units)
    assert [c["Subtract_median"] for c in channels] == [False, True]
    assert [c["Line_width"] for c in channels] == [2.0, 2.0]
    assert channels[0]["Scaling_factor"] == 321


def test_complete_derived_inherits_missing_from_source():
    """An older derived channel lacking a setting takes its source channel's value,
    not the default of whatever signal comes first."""
    names, units = ["EEG", "ACC"], ["uV", "g"]
    saved = default_channels(2, names, units)
    saved[1]["Filter_lp_enabled"] = True
    derived = dict(saved[1], derived=True, source_channel="ACC", Re_reference="EEG")
    saved.append(_without(derived, "Subtract_median", "Filter_lp_enabled", "Line_width"))
    saved[2]["Line_width"] = 4.0  # stored on the derived channel itself
    channels = complete_channels(saved, 2, names, units)
    assert channels[2]["Subtract_median"] is True
    assert channels[2]["Filter_lp_enabled"] is True
    assert channels[2]["Line_width"] == 4.0
    assert channels[2]["Re_reference"] == "EEG"


def test_complete_renames_later_duplicates_and_references_keep_the_first():
    """An older file where derived channels kept their source's name."""
    names = ["C3", "M2"]
    saved = default_channels(2, names)
    saved[1]["Re_reference"] = "C3"
    saved.append(dict(saved[0], derived=True, source_channel="C3", Re_reference="M2"))
    saved.append(dict(saved[0], derived=True, source_channel="C3", Re_reference="M2"))
    channels = complete_channels(saved, 2, names)
    assert [c["Channel_name"] for c in channels] == ["C3", "M2", "C3*", "C3**"]
    assert channels[1]["Re_reference"] == "C3"
    assert [c["source_channel"] for c in channels[2:]] == ["C3", "C3"]


def test_complete_keeps_a_derived_channel_among_ordinary_channels():
    """A derived channel moved above an ordinary channel stays there, on its source's signal."""
    names = ["C3", "C4", "M2"]
    saved = default_channels(3, names)
    saved.insert(1, derive_channel(saved, "C4", "M2"))
    channels = complete_channels(saved, 3, names)
    assert [(c["Channel_name"], c["Signal_index"]) for c in channels] == [
        ("C3", 0), ("C4*", 1), ("C4", 1), ("M2", 2)]


def test_complete_keeps_the_name_for_the_ordinary_channel_when_a_duplicate_comes_first():
    """An older file with a derived channel named like its source, placed above it."""
    names = ["C3", "M2"]
    saved = default_channels(2, names)
    saved.insert(0, dict(saved[0], derived=True, source_channel="C3", Re_reference="M2"))
    channels = complete_channels(saved, 2, names)
    assert [c["Channel_name"] for c in channels] == ["C3*", "C3", "M2"]



def test_complete_fills_signal_index_by_name_where_names_match_the_file():
    """An older file whose channels were reordered: each finds its file signal by name."""
    names = ["C3", "C4", "M2"]
    saved = [_without(c, "Signal_index") for c in reversed(default_channels(3, names))]
    saved.append(dict(saved[1], Channel_name="C4*", derived=True, source_channel="C4"))
    channels = complete_channels(saved, 3, names)
    assert [(c["Channel_name"], c["Signal_index"]) for c in channels] == [
        ("M2", 2), ("C4", 1), ("C3", 0), ("C4*", 1)]


def test_complete_fills_signal_index_by_position_when_names_do_not_match():
    """An older file with a renamed channel: file signals are taken in order."""
    names = ["C3", "C4", "M2"]
    saved = [_without(c, "Signal_index") for c in default_channels(3, names)]
    saved[0]["Channel_name"] = "Left"
    channels = complete_channels(saved, 3, names)
    assert [c["Signal_index"] for c in channels] == [0, 1, 2]


def test_complete_keeps_a_stored_signal_index():
    names = ["C3", "C4"]
    saved = default_channels(2, names)
    saved.reverse()
    saved[0]["Channel_name"] = "Right"  # renamed and moved: name no longer matches the file
    channels = complete_channels(saved, 2, names)
    assert [c["Signal_index"] for c in channels] == [1, 0]


def test_template_takes_precedence_over_defaults():
    names = ["C3", "C4", "EOG"]
    template = [dict(default_channels(1, ["C3"])[0], Scaling_factor=200, Line_width=3.5, Subtract_median=True)]
    channels = merge_template(default_channels(3, names), template)
    assert [c["Scaling_factor"] for c in channels] == [200, 50, 50]
    assert [c["Line_width"] for c in channels] == [3.5, 2.0, 2.0]
    assert [c["Subtract_median"] for c in channels] == [True, False, False]


def test_template_entry_without_newer_setting_keeps_default():
    names, units = ["EEG", "ACC"], ["uV", "g"]
    old = [_without(default_channels(2, names)[1], "Subtract_median")]
    channels = merge_template(default_channels(2, names, units), old)
    assert channels[1]["Subtract_median"] is True


def test_template_derived_recreated_only_with_source_and_completed_from_it():
    names, units = ["EEG", "ACC"], ["uV", "g"]
    template = default_channels(2, names, units)
    template[1]["Filter_hp_enabled"] = True
    derived = dict(template[1], derived=True, source_channel="ACC", Re_reference="EEG")
    orphan = dict(template[0], Channel_name="X", derived=True, source_channel="MISSING")
    template += [_without(derived, "Subtract_median", "Line_width", "Filter_hp_enabled"), orphan]
    template[2]["Line_width"] = 5.0
    channels = merge_template(default_channels(2, names, units), template)
    assert len(channels) == 3
    assert channels[2]["source_channel"] == "ACC"
    assert channels[2]["Subtract_median"] is True
    assert channels[2]["Filter_hp_enabled"] is True
    assert channels[2]["Line_width"] == 5.0
    assert channels[2]["Re_reference"] == "EEG"


def test_derived_channel_starts_with_source_settings():
    channels = default_channels(3, ["ACC", "EEG", "M2"], ["g", "uV", "uV"])
    channels[0].update(
        Filter_hp_enabled=True, Filter_hp_cutoff=0.5, Filter_lp_enabled=True, Filter_lp_order=6,
        Filter_notch_enabled=True, Filter_notch_cutoff=60.0, Scaling_factor=150, Vertical_shift=-20,
        Channel_color="Red", Line_width=3.0, Flip_polarity=True,
        Re_reference="M2", Display_on_screen=0,
    )
    source = channels[0]
    channel = derive_channel(channels, "ACC", "EEG")
    assert channel["Re_reference"] == "EEG"
    assert channel["Display_on_screen"]
    assert channel["derived"] is True and channel["source_channel"] == "ACC"
    for name in ("Filter_hp_enabled", "Filter_hp_cutoff", "Filter_lp_enabled", "Filter_lp_order",
                 "Filter_notch_enabled", "Filter_notch_cutoff", "Scaling_factor", "Vertical_shift",
                 "Channel_color", "Line_width", "Flip_polarity", "Subtract_median"):
        assert channel[name] == source[name], name
    assert channel["Subtract_median"] is True
    assert source["Re_reference"] == "M2"  # source untouched


def test_derived_channel_named_after_source_with_first_free_star():
    channels = default_channels(2, ["C3", "M2"])
    first = derive_channel(channels, "C3", "M2")
    assert first["Channel_name"] == "C3*"
    channels.append(first)
    assert derive_channel(channels, "C3", "M2")["Channel_name"] == "C3**"


def test_derived_channel_uses_source_file_signal():
    channels = default_channels(3, ["C3", "C4", "M2"])
    channels.reverse()  # moved: positions no longer match the file
    assert derive_channel(channels, "C4", "M2")["Signal_index"] == 1
    assert derive_channel(channels, "M2", "C3")["Signal_index"] == 2


def _montage():
    """C3, M2, and C3* = C3 - M2; C3 is the reference of M2 and every analysis channel."""
    channels = default_channels(2, ["C3", "M2"])
    channels[1]["Re_reference"] = "C3"
    channels.append(derive_channel(channels, "C3", "M2"))
    general = {"Channel_for_spectogram": "C3", "Wavelet_channel": "C3", "Periodogram_channel": "C3"}
    return channels, general


def test_rename_repoints_every_reference_to_the_channel():
    channels, general = _montage()
    rename_channel(channels, general, "C3", "Left")
    assert [c["Channel_name"] for c in channels] == ["Left", "M2", "C3*"]
    assert channels[1]["Re_reference"] == "Left"
    assert channels[2]["source_channel"] == "Left"
    assert general == {"Channel_for_spectogram": "Left", "Wavelet_channel": "Left", "Periodogram_channel": "Left"}


def test_rename_to_a_taken_name_is_refused_and_changes_nothing():
    channels, general = _montage()
    before = ([dict(c) for c in channels], dict(general))
    with pytest.raises(ValueError):
        rename_channel(channels, general, "C3", "M2")
    assert (channels, general) == before


def test_template_matches_by_name_and_channels_keep_their_file_signal():
    """A template saved from a recording with another signal order."""
    template = default_channels(2, ["M2", "C3"])
    template.append(dict(derive_channel(template, "C3", "M2"), Signal_index=7))
    channels = merge_template(default_channels(2, ["C3", "M2"]), template)
    assert [(c["Channel_name"], c["Signal_index"]) for c in channels] == [("C3", 0), ("M2", 1), ("C3*", 0)]


_SIGNAL_CHANGES = [
    ("Filter_hp_cutoff", 1.0), ("Filter_lp_order", 8), ("Filter_notch_enabled", True),
    ("Filter_hp_enabled", True), ("Re_reference", "C4"), ("Flip_polarity", True),
]
_DISPLAY_CHANGES = [
    ("Scaling_factor", 300), ("Line_width", 4.0), ("Subtract_median", True),
    ("Vertical_shift", 10), ("Channel_color", "Red"), ("Display_on_screen", 0),
]


def test_signal_affecting_change_changes_fingerprint():
    base = default_channels(2, ["C3", "C4"])
    for name, value in _SIGNAL_CHANGES:
        changed = [dict(base[0], **{name: value}), base[1]]
        assert rebuild_fingerprint(changed) != rebuild_fingerprint(base), name


def test_display_only_change_keeps_fingerprint():
    base = default_channels(2, ["C3", "C4"])
    for name, value in _DISPLAY_CHANGES:
        changed = [dict(base[0], **{name: value}), base[1]]
        assert rebuild_fingerprint(changed) == rebuild_fingerprint(base), name
