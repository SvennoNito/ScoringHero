"""Tests for the displayed signal module: planning what to build, reorder, drop,
restore or recompute, and building displayed rows from raw rows by Signal_index."""

import numpy as np

from config.channel_settings import default_channels, derive_channel, rename_channel
from eeg.displayed_signal import EMPTY, PARTS, build_rows, busy_label, plan, renamed


def _channels():
    """C3 feeds the spectrogram, C4 the periodograms, O1 the wavelet panel; EMG no panel."""
    return default_channels(4, ["C3", "C4", "O1", "EMG"])


def _general(**kw):
    return {
        "Sampling_rate_hz": 128, "Epoch_length_s": 30, "Extension_epoch_s": [1, 1],
        "Channel_for_spectogram": "C3", "Periodogram_channel": "C4", "Wavelet_channel": "O1",
        "Wavelet_frequency_limits_hz": [0.25, 45], **kw,
    }


def _settled(channels, general, overlay=None):
    """Stored state after everything was built and computed once."""
    return plan(EMPTY, channels, general, overlay, False, {}).state


def _built(rows):
    return [i for i, old in enumerate(rows) if old is None]


def test_move_only_reorders():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    channels.insert(0, channels.pop(2))
    p = plan(state, channels, general, None, False, {})
    assert p.rows == [2, 0, 1, 3]
    assert p.compute == () and p.restore == ()


def test_rename_after_rekeying_needs_nothing():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    rename_channel(channels, general, "C3", "Cz")
    p = plan(renamed(state, "C3", "Cz"), channels, general, None, False, {})
    assert p.rows == [0, 1, 2, 3]
    assert p.compute == () and p.restore == ()


def test_display_only_edit_builds_nothing():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    channels[0].update(Scaling_factor=300, Channel_color="Red", Display_on_screen=0, Subtract_median=True)
    p = plan(state, channels, general, None, False, {})
    assert _built(p.rows) == [] and p.compute == ()


def test_filter_on_unanalysed_channel_builds_one_row_only():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    channels[3]["Filter_hp_enabled"] = True
    p = plan(state, channels, general, None, False, {})
    assert _built(p.rows) == [3]
    assert p.compute == ()


def test_filter_on_periodogram_channel_recomputes_periodograms():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    channels[1]["Filter_lp_enabled"] = True
    p = plan(state, channels, general, None, False, {})
    assert _built(p.rows) == [1]
    assert p.compute == ("epoch_periodograms",)


def test_rereferencing_periodogram_channel_recomputes_periodograms():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    channels[1]["Re_reference"] = "O1"
    p = plan(state, channels, general, None, False, {})
    assert _built(p.rows) == [1]
    assert p.compute == ("epoch_periodograms",)


def test_filter_on_spectrogram_channel_recomputes_spectrogram_and_normalisation():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    channels[0]["Flip_polarity"] = True
    p = plan(state, channels, general, None, False, {})
    assert _built(p.rows) == [0]
    assert p.compute == ("spectrogram", "wavelet_normalisation")


def test_wavelet_channel_signal_change_refreshes_wavelet_cache():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    channels[2]["Filter_notch_enabled"] = True
    p = plan(state, channels, general, None, False, {})
    assert _built(p.rows) == [2]
    assert p.compute == ("wavelet_cache",)


def test_periodogram_channel_selector_recomputes_periodograms_only():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    general["Periodogram_channel"] = "EMG"
    p = plan(state, channels, general, None, False, {})
    assert _built(p.rows) == [] and p.compute == ("epoch_periodograms",)


def test_spectrogram_channel_selector_recomputes_spectrogram_and_normalisation():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    general["Channel_for_spectogram"] = "EMG"
    p = plan(state, channels, general, None, False, {})
    assert p.compute == ("spectrogram", "wavelet_normalisation")


def test_wavelet_limits_recompute_normalisation_and_wavelet_cache_only():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    general["Wavelet_frequency_limits_hz"] = [1, 30]
    p = plan(state, channels, general, None, False, {})
    assert _built(p.rows) == [] and p.compute == ("wavelet_normalisation", "wavelet_cache")


def test_epoch_length_recomputes_all_parts():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    general["Epoch_length_s"] = 20
    p = plan(state, channels, general, None, False, {})
    assert _built(p.rows) == [] and p.compute == PARTS


def test_add_derived_channel_builds_only_the_new_row_primary_and_overlay():
    channels, general = _channels(), _general()
    state = _settled(channels, general, overlay=1)
    channels.append(derive_channel(channels, "C3", "EMG"))
    p = plan(state, channels, general, 1, False, {})
    assert _built(p.rows) == [4] and _built(p.overlay_rows) == [4]
    assert p.rows[:4] == p.overlay_rows[:4] == [0, 1, 2, 3]
    assert p.compute == ()


def test_delete_drops_the_row():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    del channels[3]
    p = plan(state, channels, general, None, False, {})
    assert p.rows == [0, 1, 2]
    assert p.compute == ()


def test_overlay_moves_with_its_channel():
    channels, general = _channels(), _general()
    state = _settled(channels, general, overlay=1)
    channels.insert(0, channels.pop(3))
    p = plan(state, channels, general, 1, False, {})
    assert p.rows == p.overlay_rows == [3, 0, 1, 2]


def test_overlay_loaded_builds_overlay_rows_only():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    p = plan(state, channels, general, 1, False, {})
    assert _built(p.rows) == [] and _built(p.overlay_rows) == [0, 1, 2, 3]
    assert p.compute == ()


def test_overlay_removed_drops_overlay_rows():
    channels, general = _channels(), _general()
    state = _settled(channels, general, overlay=1)
    p = plan(state, channels, general, None, False, {})
    assert p.overlay_rows is None and _built(p.rows) == []


def test_switching_analysis_to_overlay_recomputes_all_parts_and_writes_no_cache():
    channels, general = _channels(), _general()
    state = _settled(channels, general, overlay=1)
    p = plan(state, channels, general, 1, True, {})
    assert p.compute == PARTS and p.write == ()


def test_empty_state_with_matching_cache_builds_all_rows_and_restores_all_parts():
    channels, general = _channels(), _general()
    cached = _settled(channels, general).parts
    p = plan(EMPTY, channels, general, None, False, cached)
    assert _built(p.rows) == [0, 1, 2, 3]
    assert p.restore == ("spectrogram", "wavelet_normalisation", "epoch_periodograms")
    assert p.compute == ("wavelet_cache",) and p.write == ()


def test_mismatched_cache_entry_recomputes_only_that_part():
    channels, general = _channels(), _general()
    cached = _settled(channels, general).parts
    general["Periodogram_channel"] = "EMG"
    p = plan(EMPTY, channels, general, None, False, cached)
    assert p.restore == ("spectrogram", "wavelet_normalisation")
    assert p.compute == ("epoch_periodograms", "wavelet_cache")
    assert p.write == ("epoch_periodograms",)


def test_filtering_an_unanalysed_channel_keeps_cache_valid():
    channels, general = _channels(), _general()
    cached = _settled(channels, general).parts
    channels[3]["Filter_hp_enabled"] = True
    p = plan(EMPTY, channels, general, None, False, cached)
    assert p.compute == ("wavelet_cache",)


def test_wavelet_channel_selector_needs_no_busy_indicator():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    general["Wavelet_channel"] = "EMG"
    p = plan(state, channels, general, None, False, {})
    assert p.compute == ("wavelet_cache",) and busy_label(p) is None


def test_busy_label_filtering_when_rows_are_built_computing_when_parts_recomputed():
    channels, general = _channels(), _general()
    state = _settled(channels, general)
    channels[3]["Filter_hp_enabled"] = True
    assert busy_label(plan(state, channels, general, None, False, {})) == "Filtering…"
    channels[3]["Filter_hp_enabled"] = False
    general["Periodogram_channel"] = "EMG"
    assert busy_label(plan(state, channels, general, None, False, {})) == "Computing…"


def test_new_overlay_signal_rebuilds_overlay_rows_and_analysed_parts():
    """Overlay signals are told apart by identity: equal arrays are still different."""
    channels, general = _channels(), _general()
    old, new = np.zeros((4, 8)), np.zeros((4, 8))
    state = plan(EMPTY, channels, general, old, True, {}).state
    same = plan(state, channels, general, old, True, {})
    assert _built(same.rows) == _built(same.overlay_rows) == [] and same.compute == ()
    p = plan(state, channels, general, new, True, {})
    assert _built(p.rows) == [] and _built(p.overlay_rows) == [0, 1, 2, 3]
    assert p.compute == PARTS


# Row building

FS = 128.0


def _raw():
    """Three file signals: a slow sine, a fast sine, a ramp."""
    t = np.arange(int(FS * 60)) / FS
    return np.array([np.sin(2 * np.pi * 1 * t), np.sin(2 * np.pi * 20 * t), t / t[-1]])


def test_row_is_raw_signal_at_signal_index():
    raw = _raw()
    channels = default_channels(3, ["A", "B", "C"])
    channels[0]["Signal_index"] = 2
    rows = build_rows(raw, channels, [0, 1], FS)
    assert np.array_equal(rows, raw[[2, 1]])


def test_rereference_against_reference_raw_row_then_flip():
    raw = _raw()
    channels = default_channels(3, ["A", "B", "C"])
    channels[0].update(Re_reference="C", Flip_polarity=True)
    channels[2]["Flip_polarity"] = True  # the reference's own settings never leak in
    rows = build_rows(raw, channels, [0], FS)
    assert np.allclose(rows[0], raw[2] - raw[0])


def test_filter_acts_on_rereferenced_signal_before_flip():
    """Low-pass at 5 Hz of (A - B) leaves -A's slow sine; B's 20 Hz is gone."""
    raw = _raw()
    channels = default_channels(3, ["A", "B", "C"])
    channels[0].update(Re_reference="B", Filter_lp_enabled=True, Filter_lp_cutoff=5.0, Flip_polarity=True)
    rows = build_rows(raw, channels, [0], FS)
    centre = slice(len(raw[0]) // 4, 3 * len(raw[0]) // 4)
    assert np.allclose(rows[0][centre], -raw[0][centre], atol=0.02)


def test_derived_channel_between_ordinary_channels_shows_its_source_signal():
    """A derived channel placed above an ordinary channel keeps its source's signal."""
    raw = _raw()
    channels = default_channels(3, ["A", "B", "C"])
    channels.insert(1, derive_channel(channels, "C", "A"))
    rows = build_rows(raw, channels, range(4), FS)
    assert np.array_equal(rows[[0, 2, 3]], raw)
    assert np.allclose(rows[1], raw[2] - raw[0])
