"""Tests for apply_changes: which general-setting changes bring the displayed signal
up to date and which take the wavelet colorbar fast path."""

from types import SimpleNamespace

import config.apply_changes as apply_changes_module
from config.apply_changes import apply_changes


def _ui(levels):
    return SimpleNamespace(
        config=[{"Wavelet_power_limits": {"Z-scored Power": [-1, 2]}}, []],
        TFWidget=SimpleNamespace(update_levels_only=levels.append),
    )


def _record_settings_changed(monkeypatch):
    calls = []
    monkeypatch.setattr(apply_changes_module, "settings_changed", lambda ui, callback=None: calls.append(ui))
    monkeypatch.setattr(apply_changes_module, "save_configuration", lambda ui: None)
    return calls


def test_wavelet_power_limits_alone_only_updates_levels(monkeypatch):
    calls, levels = _record_settings_changed(monkeypatch), []
    apply_changes(["Wavelet_power_limits"], _ui(levels))
    assert calls == [] and levels == [[-1, 2]]


def test_wavelet_power_limits_with_channel_added_brings_displayed_signal_up_to_date(monkeypatch):
    calls, levels = _record_settings_changed(monkeypatch), []
    ui = _ui(levels)
    apply_changes(["Wavelet_power_limits"], ui, channels_changed=True)
    assert calls == [ui]
