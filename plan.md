# Add "Morales" normalization mode to TF Widget

## Context
The TF widget displays Morlet wavelet power with three normalization modes. We need a fourth called **"Morales"** implementing:

```
dB_tf = 10 * log10(Activity_tf / Baseline_f)
```

Where `Baseline_f` = median **linear** power of a given frequency across all epochs (the entire night). This requires a new cached stat: the median of linear (not log) power per frequency.

---

## Changes (6 files)

### 1. `cache/load_cache.py` — add linear median baseline

After line 53 (`ui.tf_norm_rms = ...`), add:

```python
median_linear_welch = np.median(ui.power, axis=0)            # (n_freqs_welch,) linear scale
median_linear_welch = np.maximum(median_linear_welch, 1e-30)
ui.tf_norm_median_linear = np.interp(tf_freqs, ui.freqs, median_linear_welch)
```

This computes the median of `ui.power` (which is already in linear scale) across epochs, then interpolates to the Morlet frequency grid.

### 2. `config/apply_changes.py` — add linear median in freq-limits recalc

In the `if "Wavelet_frequency_limits_hz"` block (around line 74, after `ui.tf_norm_rms = ...`), add the same three lines:

```python
median_linear_welch = np.median(ui.power, axis=0)
median_linear_welch = np.maximum(median_linear_welch, 1e-30)
ui.tf_norm_median_linear = np.interp(ui.tf_freqs, ui.freqs, median_linear_welch)
```

### 3. `widgets/configurationWindow.py` line 436 — add dropdown option

Change:
```python
for option in ["Raw Power", "L2-Normalized Power", "Z-Standardized Power"]:
```
To:
```python
for option in ["Raw Power", "L2-Normalized Power", "Z-Standardized Power", "Morales"]:
```

### 4. `widgets/tfWidget.py` — add parameter + rendering branch

**4a.** Add `norm_median_linear` parameter to all three methods: `_render()`, `draw_tf()`, `update_tf()`.

Current `_render` signature (line 93):
```python
def _render(self, eeg_data, times_and_indices, this_epoch, srate, freqs,
            norm_median, norm_iqr, norm_rms, display_mode="Z-scored Power",
            freq_scale="Logarithmic", freq_limits=None,
            time_unit="Seconds", epoch_length=30, tf_channel_idx=0, channel_label=""):
```
New signature — add `norm_median_linear` after `norm_rms`:
```python
def _render(self, eeg_data, times_and_indices, this_epoch, srate, freqs,
            norm_median, norm_iqr, norm_rms, norm_median_linear=None, display_mode="Z-scored Power",
            freq_scale="Logarithmic", freq_limits=None,
            time_unit="Seconds", epoch_length=30, tf_channel_idx=0, channel_label=""):
```

Do the same for `draw_tf` (line 245) and `update_tf` (line 254), and pass `norm_median_linear` through to `_render`.

**4b.** In the linear-freq interpolation block (around line 124), add:
```python
if norm_median_linear is not None:
    norm_median_linear = np.interp(freqs_for_compute, freqs, norm_median_linear)
```
(Only needed when `freq_scale != "Logarithmic"`)

**4c.** After the `elif display_mode == "Z-Standardized Power":` block (after line 148), add:
```python
elif display_mode == "Morales":
    # dB relative to median baseline: 10 * log10(power / baseline)
    # = 10 * (log10(power) - log10(baseline))
    baseline_log = np.log10(np.maximum(norm_median_linear, 1e-30))
    power_display = 10 * (power_transformed - baseline_log[:, np.newaxis])
    levels = [-5, 5]
```

### 5. `utilities/refresh_gui.py` line 45-47 — pass new param

Current call (line 45-47):
```python
ui.TFWidget.update_tf(ui.eeg_data, ui.times, ui.this_epoch, srate, ui.tf_freqs,
                      ui.tf_norm_median, ui.tf_norm_iqr, ui.tf_norm_rms, display_mode, freq_scale, freq_limits,
                      time_unit, epoch_length, tf_channel_idx, tf_channel_label)
```
New call — insert `ui.tf_norm_median_linear` after `ui.tf_norm_rms`:
```python
ui.TFWidget.update_tf(ui.eeg_data, ui.times, ui.this_epoch, srate, ui.tf_freqs,
                      ui.tf_norm_median, ui.tf_norm_iqr, ui.tf_norm_rms, ui.tf_norm_median_linear,
                      display_mode, freq_scale, freq_limits,
                      time_unit, epoch_length, tf_channel_idx, tf_channel_label)
```

### 6. `utilities/redraw_gui.py` line 21-23 — pass new param

Same pattern as refresh_gui. Current call:
```python
ui.TFWidget.draw_tf(ui.eeg_data, ui.times, ui.this_epoch, srate, ui.tf_freqs,
                    ui.tf_norm_median, ui.tf_norm_iqr, ui.tf_norm_rms, display_mode, freq_scale, freq_limits,
                    time_unit, epoch_length, tf_channel_idx, tf_channel_label)
```
New call:
```python
ui.TFWidget.draw_tf(ui.eeg_data, ui.times, ui.this_epoch, srate, ui.tf_freqs,
                    ui.tf_norm_median, ui.tf_norm_iqr, ui.tf_norm_rms, ui.tf_norm_median_linear,
                    display_mode, freq_scale, freq_limits,
                    time_unit, epoch_length, tf_channel_idx, tf_channel_label)
```

---

## Verification
1. Run `python scoringhero.py` (devmode=1 loads example data)
2. Open Configuration > Wavelet section
3. Select "Morales" from the Normalization dropdown
4. Verify TF plot updates with dB-scaled values and colorbar shows [-5, 5] range
5. Switch between all four modes — each should render correctly
6. Change frequency limits and verify Morales still works after recalculation
