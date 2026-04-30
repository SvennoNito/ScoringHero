# Plan: ScoringHero per-epoch performance optimizations

## Context

Arrow-key navigation in ScoringHero is currently slower than it should be because several panels redo expensive work on every epoch change even though their inputs (`ui.eeg_data_display`, the event annotations, the channel configuration) have not changed since load. A previous review surfaced 10 hot spots; the user added an 11th (changing the Morlet TF colorbar limits forces a full wavelet recompute when it only needs `setLevels()`).

The fix is to cache results that are constant per session and add fast-paths that skip recomputation when only display attributes (color levels, normalization mode) change. The user has chosen a **lazy in-memory cache** strategy for the Morlet TF (raw power memoised by epoch on first visit, normalisation applied on the fly so mode switching stays fast). E2E verification is a **smoke launch with `devmode=1`**.

## Key findings from code exploration

- **Cache file**: `cache/load_cache.py` validates `{filename}.cache.pkl` against a `manipulation_fingerprint` (filter / re-ref / flip per channel) plus sampling rate, epoch length, spectrogram channel. Spectrogram and TF norm stats are already persisted there. `recompute_derived.py` is the single orchestrator that recomputes everything when `eeg_data_display` changes.
- **Morlet TF call site**: `widgets/tfWidget.py:_render` (called via `update_tf` from `utilities/tf_config_helper.py`) runs `compute_morlet_tf()` on every navigation. The `L2normalize=True` path is enabled only for the `"Z-Standardized Power"` display mode (line 161). The L2 scale factor depends only on `(srate, freqs, n_samples_per_extended_epoch)` — all session-constant — so it can be precomputed once and applied on the fly.
- **Hypnogram**: `widgets/hypnogramWidget.py:update_events` is called from `utilities/refresh_gui.py:15` on every navigation but the only event mutators (`events/event_handler.py`, `add_events_to_container.py`, `erase_events_in_rectangles.py`, `relabel_event.py`, `drop_event.py`) already call it themselves. The navigation call is redundant.
- **Welch periodogram**: `signal_processing/compute_epoch_periodogram.py:welch()` is the most expensive non-TF per-navigation cost. Cache size for all epochs of one channel is small (~8 MB for an 8h recording).
- **Channel-name → index**: 6 call sites use `channel_names.index()` (`load_wrapper.py`, `tf_config_helper.py`, `compute_epoch_periodogram.py`, `spectogram_to_ui.py`, `open_seed_window.py`, `open_mt_kcd_window.py`) and rebuild the list every call.
- **Visible channels**: filtered by `Display_on_screen` in `signalWidget.py:58`, `signalWidget.py:268`, `score_stage.py:22`, and `channel_from_selection.py`.
- **Event-in-epoch**: `container.epochs` is a list-of-lists. `events/draw_event_in_this_epoch.py:8` does an O(k) `in` test per border per navigation. Mutators that rebuild it: `event_handler.py:39`, `add_events_to_container.py:13`, `erase_events_in_rectangles.py:33`, `relabel_event.py:31`, `drop_event.py:10`, `setup_ui.py:480`, `events_to_ui.py:20`. `clean_epochs_to_uistages.py:4` also has a variable-shadowing bug (uses `container` as both the param and the loop var).
- **Colorbar**: both `widgets/spectogramWidget.py:113-122` and `widgets/tfWidget.py:248-263` rebuild the gradient `np.linspace(...).reshape(-1,1) + np.repeat(...)` on every render. Spectrogram changes also funnel through `apply_changes.py:51-52` which calls `draw_spectogram` (full redraw) for `Spectrogram_power_limits` change; the TF equivalent also triggers a full `redraw_gui` which includes a Morlet recompute.

---

## Work units

### Unit 1 — Morlet TF lazy cache + normalization split + colorbar fast-paths
**Impact: HIGH**

**Files**: `widgets/tfWidget.py`, `signal_processing/compute_morlet_tf.py`, `signal_processing/recompute_derived.py`, `config/apply_changes.py`, `eeg/load_wrapper.py`, `utilities/tf_config_helper.py`

**Changes**:
- Drop the `L2normalize` parameter from `compute_morlet_tf` — always return unnormalised power.
- In `recompute_derived.py`, precompute and store:
  - `ui.tf_l2_scale_sq` — `(n_freqs,)` array. For each freq build the same wavelet kernel used during the FFT-convolution, compute `np.sum(wavelet_fft**2)`, store as `scale_sq`. Used by Z-Standardized mode to divide the cached raw power.
  - `ui.tf_norm_median_lin_grid`, `ui.tf_norm_iqr_lin_grid`, `ui.tf_norm_rms_lin_grid` — linear-frequency-axis interpolations of the norm stats that `tfWidget._render` lines 150-156 currently rebuild every epoch. Compute once alongside the existing log-axis stats.
  - Set `ui.tf_cache = {}` here (both initialises and clears it on any filter/re-ref change).
- In `tfWidget._render`:
  - Look up `ui.tf_cache[this_epoch]` for cached raw `(n_freqs, n_ext)` float32 power. On miss, compute via `compute_morlet_tf(signal, srate, freqs)` and store float32-cast result.
  - Apply L2 norm in-place by dividing `power_raw` by `ui.tf_l2_scale_sq[:, None]` only when `display_mode == "Z-Standardized Power"`.
  - When `freq_scale == "Linear"`, use the precomputed linear-grid norm stats from `ui` instead of `np.interp` per call.
  - Cache the colorbar gradient on the widget: store `self._cbar_gradient_cache = (cbar_height_int, cbar_width, levels, gradient_array)` and rebuild only when any of those inputs change.
  - Add `update_levels_only(levels)` public method: calls `self.img.setLevels(levels)`, `self._cbar_img.setLevels(levels)`, rebuilds gradient if levels changed, updates label text. No Morlet recompute, no reslice.
- Update `draw_tf` / `update_tf` signatures to pass `ui` (or the new cache/norm attributes) and update callers in `tf_config_helper.py:call_tf_widget` and `eeg/load_wrapper.py:125`.
- In `config/apply_changes.py`:
  - Add an explicit `"Wavelet_power_limits"` clause that calls `ui.TFWidget.update_levels_only(...)` and skips `redraw_gui`.
  - In the `"Wavelet_frequency_limits_hz"` clause, also clear `ui.tf_cache`, recompute `ui.tf_l2_scale_sq`, and update the linear-grid norm stats.
  - Add a `"Wavelet_channel"` clause that clears `ui.tf_cache` and calls `redraw_gui` (no full `recompute_derived` needed).

**Addresses**: items 1, 9, 10-tf, and the new colorbar-limits complaint.

---

### Unit 2 — Spectrogram colorbar fast-path + gradient cache
**Impact: HIGH (for colorbar changes) / LOW (for navigation)**

**Files**: `widgets/spectogramWidget.py`, `config/apply_changes.py`

**Changes**:
- Add `update_levels_only(levels)` to `SpectogramWidget`: calls `self.img.setLevels`, `self._cbar_img.setLevels`, updates min/max text, rebuilds gradient only if levels changed.
- Cache the gradient on the widget: `self._cbar_gradient_cache = (cbar_height_int, cbar_width, levels, gradient_array)`.
- In `apply_changes.py:51-52`, when only `"Spectrogram_power_limits"` changed, call `ui.SpectogramWidget.update_levels_only(new_levels)` instead of `draw_spectogram`.

**Addresses**: item 10-spec and the spectrogram colorbar limits complaint.

---

### Unit 3 — Hypnogram event redraw decoupling + np.unique flatten
**Impact: HIGH**

**Files**: `widgets/hypnogramWidget.py`, `utilities/refresh_gui.py`

**Changes**:
- Remove `ui.HypnogramWidget.update_events(ui)` from `utilities/refresh_gui.py:15`. All event mutators already call it themselves; navigation never changes event data.
- Replace line 97 `np.array(list(set(chain.from_iterable(container.epochs)))) - 1` with `np.unique(np.concatenate(container.epochs)).astype(int) - 1`, guarded by `if container.epochs else np.array([], dtype=int)`.
- Remove the now-unused `from itertools import chain` import.

**Addresses**: items 2 and 7.

---

### Unit 4 — Welch periodogram precompute and dict lookup
**Impact: HIGH**

**Files**: `signal_processing/compute_epoch_periodogram.py`, `signal_processing/recompute_derived.py`, `cache/ui_to_cache.py`, `cache/load_cache.py`, `utilities/refresh_gui.py`, `config/apply_changes.py`

**Changes**:
- Add `precompute_all_epoch_periodograms(ui)` — runs `welch` for every epoch on the periodogram channel, stores raw `(n_epochs, n_freqs)` power on `ui.epoch_periodogram_power` and `ui.epoch_periodogram_freqs`. Called from `recompute_derived.py`.
- Refactor `compute_epoch_periodogram(ui, epoch_idx)` to read from `ui.epoch_periodogram_power[epoch_idx]` instead of calling `welch`, then apply the display-mode trim/scale as before. The return signature `(freqs, power, channel_name)` is unchanged.
- Persist to `{filename}.cache.pkl` via `cache/ui_to_cache.py` under key `"epoch_periodogram"` with sub-keys `power`, `freqs`, `channel`, `Sampling_rate_hz`. Validate in `cache/load_cache.py` against sampling rate, channel name, and manipulation fingerprint; recompute via `precompute_all_epoch_periodograms` if invalid.
- In `apply_changes.py`, when `"Periodogram_channel"` or `"Sampling_rate_hz"` changes, call `precompute_all_epoch_periodograms`. When only `"Periodogram_limit_hz"` or `"Periodogram_display_mode"` changes, the existing call to `compute_epoch_periodogram(ui, ui.this_epoch)` is already correct (trim/scale only).

**Addresses**: item 3.

---

### Unit 5 — AnnotationContainer epoch sets
**Impact: MEDIUM**

**Files**: `widgets/annotationContainer.py`, `events/event_epoch.py`, `events/draw_event_in_this_epoch.py`, `events/event_handler.py`, `events/add_events_to_container.py`, `events/erase_events_in_rectangles.py`, `events/relabel_event.py`, `events/drop_event.py`, `ui/setup_ui.py`, `scoring/events_to_ui.py`, `scoring/clean_epochs_to_uistages.py`

**Changes**:
- Add `self.epochs_set: list[set[int]] = []` next to `self.epochs` in `AnnotationContainer.__init__`.
- At every site that writes `container.epochs` (full rebuild via `event_epoch`), add `container.epochs_set = [set(lst) for lst in container.epochs]` immediately after.
- For `drop_event.py:10` and `relabel_event.py:31` (which use `.pop(index)`), also pop the same index from `epochs_set`.
- For `events_to_ui.py:20` (`.epochs.append(...)`), also append `set(container["epoch"])` to `epochs_set`.
- Replace `draw_event_in_this_epoch.py:7-10` to test `(ui.this_epoch + 1) in epoch_set` against `container.epochs_set`.
- Fix the variable-shadowing bug in `clean_epochs_to_uistages.py:4` (`any(epoch+1 in container for container in container.epochs)` rebinds `container` — rename inner var to `ep`) and use `epochs_set`.

**Addresses**: item 6, incidentally fixes a bug.

---

### Unit 6 — Cached channel-name → index map
**Impact: MEDIUM**

**Files**: `eeg/load_wrapper.py`, `config/apply_changes.py`, `utilities/tf_config_helper.py`, `signal_processing/compute_epoch_periodogram.py`, `signal_processing/spectogram_to_ui.py`, `scoring/open_seed_window.py`, `scoring/open_mt_kcd_window.py`

**Changes**:
- Add `utilities/channel_index.py` with `rebuild_channel_index(ui)` → `ui.channel_name_to_idx = {ch["Channel_name"]: i for i, ch in enumerate(ui.config[1])}`.
- Call it from `eeg/load_wrapper.py` after `ui.config = load_configuration(...)` and from `config/apply_changes.py` in the `channel_settings_changed` branch (and after any channel reorder).
- Replace all 6 `channel_names.index(...)` / `channel_labels.index(...)` patterns with `ui.channel_name_to_idx.get(name, 0)`.

**Addresses**: item 4.

---

### Unit 7 — Cached visible-channel index list
**Impact: MEDIUM**

**Files**: `widgets/signalWidget.py`, `eeg/load_wrapper.py`, `config/apply_changes.py`

**Changes**:
- Add `rebuild_visible_channels(ui)` (can go in the same `utilities/channel_index.py` as Unit 6) → `ui.visible_channel_idx = [i for i, ch in enumerate(ui.config[1]) if ch["Display_on_screen"]]`.
- Call it from `load_wrapper.py` after config load and from `apply_changes.py` whenever channel settings change.
- In `signalWidget.draw_signal` (line 57-59) and `signalWidget.update_signal` (line 267-269), read `ui.visible_channel_idx` instead of filtering `config[1]` inline. The list is passed through to the widget alongside the rest of the `ui` data; refactor the call sites accordingly if needed.

**Addresses**: item 5.

---

### Unit 8 — `min_max_scale` numpy-vectorise + zero-range guard
**Impact: LOW / QUICK WIN**

**Files**: `signal_processing/min_max_scale.py`

**Changes**:
- Rewrite as:
  ```python
  import numpy as np
  def min_max_scale(values):
      lo = np.min(values)
      span = np.ptp(values)
      return (values - lo) / span if span > 0 else np.zeros_like(values, dtype=float)
  ```

**Addresses**: item 8. Fixes silent divide-by-zero and replaces two Python-level `min`/`max` traversals with a single vectorised pass.

---

## Conflict-prone shared files

Workers must rebase/merge carefully on these files since multiple units touch them:

| File | Units |
|------|-------|
| `signal_processing/recompute_derived.py` | 1, 4 |
| `cache/load_cache.py`, `cache/ui_to_cache.py` | 1, 4 |
| `utilities/refresh_gui.py` | 3, 4 |
| `config/apply_changes.py` | 1, 2, 4, 6, 7 |
| `eeg/load_wrapper.py` | 1, 6, 7 |
| `signal_processing/compute_epoch_periodogram.py` | 4, 6 |
| `utilities/tf_config_helper.py` | 1, 6 |

Conflicts are mostly localised additions to separate sections; git's 3-way merge should handle them. Units 6 and 7 can share a new `utilities/channel_index.py` file — whichever lands first creates it; the second adds its function.

## End-to-end test recipe (smoke launch)

The project has no automated tests (per `CLAUDE.md`). Verify with a smoke launch:

1. In the worktree, run `uv sync` if `.venv` is absent.
2. Temporarily set `self.devmode = 1` in `scoringhero.py:139`.
3. Launch with a wall-clock timeout and capture output:
   ```bash
   # On Windows bash:
   uv run scoringhero.py &
   PID=$!
   sleep 20
   kill $PID 2>/dev/null
   ```
4. Verify: no `Traceback` / `Error` in the output and `@timing_decorator` log lines appear for `setup_ui`, `draw_signal`, `draw_hypnogram`.
5. Revert `devmode` to `0` before committing.
