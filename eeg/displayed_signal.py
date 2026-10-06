"""Displayed signal: owns the displayed signal of the primary recording and of the
overlay signal (ui.eeg_data_display, ui.eeg_data_display_ref, rows in channel-list
order) and the analysis data derived from it (spectrogram + SWA, wavelet
normalisation, epoch periodograms, wavelet power cache).

Two entries:
- settings_changed(ui, callback=None): call after anything the displayed signal or
  the analysis data depend on may have changed (channel settings, filters, adding,
  deleting or moving channels, analysis-relevant general settings, loading or
  removing the overlay signal, switching the analysis source, opening a recording).
  Works out the minimum work, does it (under the busy indicator if rows are built
  or analysis parts recomputed), redraws, saves the configuration, then calls
  callback.
- channel_renamed(ui, old_name, new_name): instant rename; rebuilds nothing.

Raw data (ui.eeg_data, ui.eeg_data_ref) stays as loaded, in file order; each
displayed row is built from the raw row at the channel's Signal_index.
"""

from collections import namedtuple

import numpy as np

from cache.write_cache import read_cache, write_cache
from config.channel_settings import displayed_signal_inputs, rename_channel
from config.write_configuration import save_configuration
from filter.apply_filter import apply_filter
from signal_processing.compute_epoch_periodogram import (
    compute_epoch_periodogram,
    precompute_all_epoch_periodograms,
)
from signal_processing.freqs_of_interest import freqs_of_interest
from signal_processing.spectogram_to_ui import spectogram_to_ui
from utilities.busy_indicator import run_busy
from utilities.channel_index import rebuild_channel_index
from utilities.redraw_gui import redraw_all, redraw_gui

# Analysis parts in dependency order: the wavelet normalisation uses the spectrogram
PARTS = ("spectrogram", "wavelet_normalisation", "epoch_periodograms", "wavelet_cache")

# What the displayed rows and analysis parts were last built from:
# order: channel names in row order; rows / overlay_rows: per channel name, the
# inputs its primary / overlay row was built from; parts: per part, its inputs.
State = namedtuple("State", "order rows overlay_rows parts")
EMPTY = State((), {}, {}, {})

# rows / overlay_rows: per channel (new row order) the stored row to keep, or None
# to build it (overlay_rows is None without an overlay signal); stored rows not
# listed are dropped. restore / compute: analysis parts to take from the disk
# cache / to recompute; write: parts to write to the disk cache. state: the stored
# state once the plan is carried out.
Plan = namedtuple("Plan", "rows overlay_rows restore compute write state")


def _part_inputs(rows, general, source):
    """Inputs of each analysis part. A missing analysis channel means the first."""
    first = next(iter(rows.values()), None)

    def channel(key):
        return rows.get(general.get(key), first)

    epoching = (general["Sampling_rate_hz"], general["Epoch_length_s"], tuple(general["Extension_epoch_s"]))
    wavelet_limits = tuple(general.get("Wavelet_frequency_limits_hz", (0.25, 45)))
    spectrogram = (channel("Channel_for_spectogram"), epoching, source)
    return {
        "spectrogram": spectrogram,
        "wavelet_normalisation": (spectrogram, wavelet_limits),
        "epoch_periodograms": (channel("Periodogram_channel"), epoching, source),
        "wavelet_cache": (channel("Wavelet_channel"), epoching, wavelet_limits, source),
    }


def plan(state, channels, general, overlay, analyse_overlay, cached):
    """What to drop, reorder, build, restore or recompute to bring the stored state
    to the current channel list and general settings.

    overlay: token identifying the loaded overlay signal, None without one.
    analyse_overlay: the analysis parts are computed from the overlay signal.
    cached: per analysis part, the inputs of its disk cache entry."""
    srate = general["Sampling_rate_hz"]
    rows = {name: (inputs, srate) for name, inputs in displayed_signal_inputs(channels).items()}
    order = tuple(c["Channel_name"] for c in channels)
    position = {name: i for i, name in enumerate(state.order)}

    def kept(stored, current):
        return [position[n] if n in stored and stored[n] == current[n] else None for n in order]

    overlay_rows = {} if overlay is None else {n: (rows[n], overlay) for n in order}
    source = ("overlay", overlay) if analyse_overlay and overlay is not None else "original"
    parts = _part_inputs(rows, general, source)
    stale = [p for p in PARTS if state.parts.get(p) != parts[p]]
    restore = tuple(p for p in stale if p in _PART_DATA and cached.get(p) == parts[p])
    compute = tuple(p for p in stale if p not in restore)
    write = tuple(p for p in compute if p in _PART_DATA) if source == "original" else ()
    return Plan(
        kept(state.rows, rows),
        None if overlay is None else kept(state.overlay_rows, overlay_rows),
        restore, compute, write,
        State(order, rows, overlay_rows, parts),
    )


def renamed(state, old_name, new_name):
    """state with channel old_name re-keyed to new_name; its inputs are name-free."""
    def rekey(stored):
        return {new_name if n == old_name else n: v for n, v in stored.items()}

    return state._replace(
        order=tuple(new_name if n == old_name else n for n in state.order),
        rows=rekey(state.rows),
        overlay_rows=rekey(state.overlay_rows),
    )


def build_rows(raw, channels, positions, srate):
    """Displayed rows of channels[positions] from raw (file signals x samples): the
    raw row at the channel's Signal_index minus the raw row at its reference's
    Signal_index, then filtered, then polarity-flipped."""
    signal_index = {c["Channel_name"]: c["Signal_index"] for c in channels}
    selected = [channels[i] for i in positions]
    rows = np.empty((len(selected), raw.shape[1]), dtype=raw.dtype)
    for row, channel in zip(rows, selected):
        reference = signal_index.get(channel["Re_reference"])
        if reference is None:
            row[:] = raw[channel["Signal_index"]]
        else:
            np.subtract(raw[channel["Signal_index"]], raw[reference], out=row)
    if any(c[f"Filter_{kind}_enabled"] for c in selected for kind in ("hp", "lp", "notch")):
        rows = apply_filter(rows, srate, selected)
    for row, channel in zip(rows, selected):
        if channel["Flip_polarity"]:
            np.negative(row, out=row)
    return rows


def _assembled(displayed, keep, raw, channels, srate):
    """Displayed rows in the new order: kept rows from displayed, the others built."""
    build = [i for i, old in enumerate(keep) if old is None]
    if not build and keep == list(range(len(displayed))):
        return displayed
    result = np.empty((len(keep), raw.shape[1]), dtype=raw.dtype)
    kept = [i for i, old in enumerate(keep) if old is not None]
    if kept:
        result[kept] = displayed[[keep[i] for i in kept]]
    if build:
        result[build] = build_rows(raw, channels, build, srate)
    return result


def _compute_wavelet_normalisation(ui):
    """Per-frequency log-power statistics of the spectrogram on the wavelet grid."""
    limits = ui.config[0].get("Wavelet_frequency_limits_hz", [0.25, 45])
    srate = ui.config[0]["Sampling_rate_hz"]
    ui.tf_freqs = np.geomspace(max(float(limits[0]), 0.1), min(float(limits[1]), srate / 2 - 0.25), 120)
    log_power = np.log10(np.maximum(ui.power, 1e-30))
    iqr = np.percentile(log_power, 75, axis=0) - np.percentile(log_power, 25, axis=0)
    rms = np.sqrt(np.mean(log_power ** 2, axis=0))
    ui.tf_norm_median = np.interp(ui.tf_freqs, ui.freqs, np.median(log_power, axis=0))
    ui.tf_norm_iqr = np.interp(ui.tf_freqs, ui.freqs, np.maximum(iqr, 1e-6))
    ui.tf_norm_rms = np.interp(ui.tf_freqs, ui.freqs, np.maximum(rms, 1e-6))
    ui.tf_norm_median_linear = np.interp(ui.tf_freqs, ui.freqs, np.maximum(np.median(ui.power, axis=0), 1e-30))


def _compute_spectrogram(ui):
    ui.power, ui.freqs, ui.freqsOI, ui.swa = spectogram_to_ui(ui)


def _reset_wavelet_cache(ui):
    ui.tf_cache = {}


_COMPUTE = {
    "spectrogram": _compute_spectrogram,
    "wavelet_normalisation": _compute_wavelet_normalisation,
    "epoch_periodograms": precompute_all_epoch_periodograms,
    "wavelet_cache": _reset_wavelet_cache,
}

# ui attributes holding the data of each part kept in the disk cache
_PART_DATA = {
    "spectrogram": ("power", "freqs", "swa"),
    "wavelet_normalisation": ("tf_freqs", "tf_norm_median", "tf_norm_iqr", "tf_norm_rms", "tf_norm_median_linear"),
    "epoch_periodograms": ("epoch_periodogram_freqs", "epoch_periodogram_power"),
}


class _Store:
    """The module's state for one opened recording (one primary raw array). disk
    mirrors the disk cache: per part, (inputs, data)."""

    def __init__(self, raw, disk):
        self.raw = raw
        self.overlay = None  # keeps the overlay raw array (and so its token) alive
        self.state = EMPTY
        self.disk = disk


def _store(ui):
    """The current recording's store; a newly opened recording starts empty, with
    the entries of its disk cache file (an old-layout file has none)."""
    store = getattr(ui, "_displayed_signal", None)
    if store is None or store.raw is not ui.eeg_data:
        cache = read_cache(ui)
        disk = {p: cache[p] for p in _PART_DATA if isinstance(cache.get(p), tuple) and len(cache[p]) == 2}
        store = ui._displayed_signal = _Store(ui.eeg_data, disk)
    return store


def _execute(ui, store, p):
    """Carry out plan p (pure compute, no GUI objects: may run on a worker thread)."""
    channels, srate = ui.config[1], ui.config[0]["Sampling_rate_hz"]
    ui.eeg_data_display = _assembled(
        getattr(ui, "eeg_data_display", None), p.rows, ui.eeg_data, channels, srate)
    ui.eeg_data_display_ref = None if p.overlay_rows is None else _assembled(
        ui.eeg_data_display_ref, p.overlay_rows, ui.eeg_data_ref, channels, srate)
    store.overlay = ui.eeg_data_ref
    store.state = store.state._replace(order=p.state.order, rows=p.state.rows, overlay_rows=p.state.overlay_rows)

    for part in PARTS:
        if part in p.restore:
            for name, value in store.disk[part][1].items():
                setattr(ui, name, value)
        elif part in p.compute:
            _COMPUTE[part](ui)
    if "spectrogram" in p.restore:
        ui.freqsOI = freqs_of_interest(ui.freqs, ui.config)

    for part in p.write:
        store.disk[part] = (p.state.parts[part], {name: getattr(ui, name) for name in _PART_DATA[part]})
    if p.write:
        write_cache(ui, store.disk)
    store.state = p.state


def settings_changed(ui, callback=None):
    """Bring the displayed signal and the analysis data up to date with the current
    settings, doing only the work required; then redraw, save the configuration
    and call callback."""
    store = _store(ui)
    rebuild_channel_index(ui)  # the analysis parts look their channel up by name
    overlay = getattr(ui, "eeg_data_ref", None)
    p = plan(
        store.state, ui.config[1], ui.config[0],
        None if overlay is None else id(overlay),
        getattr(ui, "analysis_source", "original") == "overlay",
        {part: entry[0] for part, entry in store.disk.items()},
    )

    def done(_=None):
        if p.restore or p.compute:
            redraw_all(ui)
        else:
            redraw_gui(ui)
        save_configuration(ui)
        if callback is not None:
            callback()

    builds = None in p.rows or (p.overlay_rows is not None and None in p.overlay_rows)
    if builds or p.compute:
        run_busy(ui, "Filtering…" if builds else "Computing…", lambda: _execute(ui, store, p), done)
    else:
        _execute(ui, store, p)
        done()


def channel_renamed(ui, old_name, new_name):
    """Rename channel old_name to new_name (see channel_settings.rename_channel) and
    refresh the names shown; nothing is rebuilt or recomputed."""
    rename_channel(ui.config[1], ui.config[0], old_name, new_name)
    store = getattr(ui, "_displayed_signal", None)
    if store is not None:
        store.state = renamed(store.state, old_name, new_name)
    rebuild_channel_index(ui)
    redraw_gui(ui)
    freqs, power, channel_name = compute_epoch_periodogram(ui, ui.this_epoch)
    ui.RectanglePower.update_powerline(freqs, power, channel_name)
    save_configuration(ui)
