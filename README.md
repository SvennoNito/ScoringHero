# ScoringHero — Open-Source Sleep EEG Visualization, Annotation & Scoring

**ScoringHero** is an open-source tool (PySide6/Qt6, cross-platform) for visualizing long EEG recordings, marking events (spindles, artefacts, anything) and scoring sleep. Used by multiple labs.

![ScoringHero Main Window](screenshots/main.png)

## Getting Started

**Download:** grab the file for your OS from [Releases](https://github.com/SvennoNito/ScoringHero/releases) (Windows `.exe`; macOS `arm64` / `x86_64`) and run it. No installation.

**macOS:** the app is not Apple-registered. Run `chmod +x scoringhero_macOS_<arch>` in Terminal, then System Settings → Privacy & Security → **Open Anyway**.

**From source** (needs [uv](https://docs.astral.sh/uv/getting-started/installation/), Python 3.14.3):

```bash
git clone https://github.com/SvennoNito/ScoringHero.git
cd ScoringHero
uv sync
uv run scoringhero.py
```

**Build binaries:** Windows `uv sync --extra build-win && ./build-win.bat` (→ `dist/scoringhero.exe`); macOS `uv sync --extra build-mac && arch -arm64 ./release-mac.sh` (or `-x86_64`).

**Code signing:** free signing by [SignPath.io](https://about.signpath.io/), certificate by [SignPath Foundation](https://signpath.org/). ScoringHero runs fully locally and sends no data.

---

<table>
  <tr>
    <td width="50%"><img src="screenshots/signal_panel.png" alt="EEG signal panel" /><br /><b>Signal</b> — multi-channel EEG, stage shown in a movable badge</td>
    <td width="50%"><img src="screenshots/hypnogram_panel.png" alt="Hypnogram with SWA" /><br /><b>Hypnogram</b> — stages, events, slow-wave activity</td>
  </tr>
  <tr>
    <td width="50%"><img src="screenshots/spectrogram_panel.png" alt="Spectrogram" /><br /><b>Spectrogram</b> — click to jump to that time</td>
    <td width="50%"><img src="screenshots/periodogram_panel.png" alt="Periodogram" /><br /><b>Periodogram</b> — epoch or selected region</td>
  </tr>
  <tr>
    <td width="50%"><img src="screenshots/wavelet_panel.png" alt="Wavelet panel" /><br /><b>Time-frequency</b> — Morlet wavelet power</td>
    <td width="50%"><img src="screenshots/events_on_signal.png" alt="Events on the signal" /><br /><b>Events</b> — draw, label, relabel on the signal</td>
  </tr>
</table>

---

## Features

### Signal display
- Multiple channels with per-channel scaling, shift, color, line width; amplitude reference lines, 1 s grid
- Time axis in seconds, minutes, hours or clock time (set the recording start in the configuration)
- **Stack channels** on one baseline, or **robustly z-standardize** (median/IQR) to compare channels

<p align="center">
    <img src="screenshots/signal_stacked.png" width="49%" alt="Stacked channels" />
    <img src="screenshots/signal_zscore.png" width="49%" alt="Robustly z-standardized channels" />
</p>

- **Filtering** (`Ctrl+F`): per-channel high-pass, low-pass and notch (zero-phase Chebyshev II), with a live magnitude response. Cutoff is the −3 dB point; order sets roll-off. Filters affect the displayed signal and all derived spectra.
- **Zoom**: draw a rectangle and press `Z`.

![Filter window](screenshots/filter.png)

### Scoring
- Keys: `W`, `1`, `2`, `3`, `R`, `I` (Inconclusive), `Delete` clears, `Q` flags an epoch as uncertain
- The **stage badge** over the EEG shows the current stage (drag it anywhere; size and visibility in Configuration → General). With a comparison loaded and disagreeing it reads e.g. *N2 vs N3* with a red border.
- The status bar shows epoch (click, type a number, Enter to jump), stage, confidence, clock time, EEG and scoring file.

![Stage badge](screenshots/stage_badge.png)

### Navigation
`←`/`→` step epochs; jumps wrap around. The left navigation bar has one button per jump: next **unscored**, **uncertain** (confidence < 0.5), **stage transition**, **event**, **human-scored**, **disagreement** (needs comparison). Clicking the hypnogram or spectrogram jumps to that time.

### Events
- 13 types: Artefact (`A`) + 12 customizable (`F1`–`F12`) with own names and colors
- Draw by click-and-drag (live duration/amplitude), press the key to assign; overlapping same-type events merge
- Double-click an event to remove it; hold a key and click an event to relabel it; `Backspace` erases events inside the drawn selection
- Shown on signal and hypnogram

### Compare scoring
**Compare → Scoring → Import scoring for comparison.** Disagreements are highlighted in the hypnogram, the *Next disagreement* jump uses them, and a statistics window shows Cohen's kappa and per-stage agreement.

<p align="center">
    <img src="screenshots/compare_scoring.png" width="45%" alt="Comparison statistics" />
    <img src="screenshots/compare_hypnogram.png" width="45%" alt="Hypnogram with disagreements" />
</p>

### Spectral panels
- **Spectrogram**: Welch PSD of the full night (4 s Hann, 2 s hop), cached; channel, frequency range, power limits and colormap configurable
- **Hypnogram**: color-coded stages, events, and a **slow-wave activity** overlay (delta 0.5–4 Hz, smoothing slider)
- **Periodogram**: Welch spectrum of the epoch or of a rectangle drawn on the signal; modes 1/f removed, dB, raw
- **Wavelet**: complex Morlet via FFT convolution, adaptive cycles (3 to f/2), padded epoch against edge artifacts; 4 normalizations (raw, L2, z, dB median baseline), linear/log axis, optional ridge, can be hidden

### Automatic detection and scoring
- **MT-KCD / MT-Spindle** (`Ctrl+K`, Detectors menu): multitaper K-complex and spindle detection with amplitude/slope thresholds, optional stage restriction; results become normal events.

<p align="center">
    <img src="screenshots/mt_kcd.png" width="40%" alt="MT-KCD window" />
    <img src="screenshots/mt_spindle.png" width="40%" alt="MT-Spindle window" />
</p>

- **GSSC** (`Ctrl+G`): Greifswald Sleep Stage Classifier for scalp EEG/EOG; optional 0.3–30 Hz bandpass.
- **NIDRA ezscore-f** (`Ctrl+N`): artifact-aware scoring for two-channel forehead EEG ([Coon et al. 2025](https://doi.org/10.1101/2025.06.02.657451), ONNX models from [NIDRA](https://github.com/paulzerr/nidra), weights downloaded on first use). Artifact epochs are left unscored/Inconclusive and flagged; can store hypnodensity. Needs `uv sync --extra nidra`, see [NIDRA_SETUP.md](NIDRA_SETUP.md).

<p align="center">
    <img src="screenshots/GSSC.png" width="30%" alt="GSSC window" />
    <img src="screenshots/NIDRA.png" width="35%" alt="NIDRA window" />
</p>

Predictions are imported as a scoring you can review, correct and export.

### Sleep report (PDF)
**File → Export → Sleep Report**: hypnogram, whole-night spectrogram, example EEG trace, TST/TRT/efficiency, stage distribution, N2/N3/REM latencies.

![Sleep report page](screenshots/report_page.png)

---

## Configuration

`Ctrl+C`; saved per recording as `{filename}.config.json`.

- **General**: sampling rate, epoch length, channel distance, reference line, wavelet padding, time unit, recording start, stage badge
- **Channels**: name, visibility, color, scaling, shift, line width; stack / z-standardize
- **Events**: names, colors, counts and durations, delete per type
- **Spectrogram / Periodogram / Wavelet**: channel, frequency limits, power limits, mode, colormap

<p align="center">
    <img src="screenshots/general_config.png" width="32%" alt="General tab" />
    <img src="screenshots/channel_config.png" width="32%" alt="Channels tab" />
    <img src="screenshots/event_config.png" width="32%" alt="Events tab" />
</p>

---

## File Formats

### EEG import

| Format | Ext. | Notes |
|--------|------|-------|
| EEGLAB | `.mat` | v5 and v7.3 (HDF5); needs `EEG.data` (channels × samples; transposed auto-fixed), `EEG.srate`, `EEG.chanlocs(i).labels` (missing → `CH1…`) |
| EDF | `.edf` | via pyedflib; a Volt-scaled variant converts to µV |
| Zurich R09 | `.r09` | legacy; fixed 9 channels at 128 Hz (`F3-A2, F4-A1, C3-A2, C4-A1, O1-A2, O2-A1, EOG1, EOG2, EMG`), `int16` |

### Scoring import

| Format | Ext. | Encoding |
|--------|------|----------|
| ScoringHero | `.json` | native: stages, events, confidence |
| YASA | `.txt` | one token per line: `W/WAKE`, `N1/NREM1/1`, `N2/NREM2/2`, `N3/NREM3/3`, `R/REM/4` |
| Sleeptrip | `.csv` | numeric column: 0 W, 1 N1, 2 N2, 3 N3, 5 REM |
| Sleepyland | `.annot` | tab-separated, col 1 stage (`W N1 N2 N3 R`), col 5 `pW=..;pN1=..;…` used as confidence |
| GSSC | `.csv` | header `Epoch, Time, Stage, Conf_W, …, Conf_R`; 0 W, 1 N1, 2 N2, 3 N3, 4 REM |
| Zurich VIS | `.vis` | first line offset, then `<epoch> <code> [comment]`; `0 1 2 3 r`, `e` = repeat previous; 20 s epochs |

Epoch-count and stage-name mismatches are checked for every format: one extra/missing epoch is dropped/filled with a warning; more asks to cancel or truncate/copy the last epoch; unknown stages ask to cancel or set *unscored*.

### Native JSON

Saved as `{filename}.json` next to the EEG: `[ <stages>, <annotations> ]`.

```json
{"epoch": 1, "start": 0, "end": 30, "stage": "N2", "digit": -2,
 "confidence": 0.85, "channels": ["C3"], "clean": 1, "source": "YASA"}
```
`stage` (wins on load): `Wake` 1, `N1` −1, `N2` −2, `N3` −3, `REM` 0, `Inconclusive` 2, `null` unscored. `epoch`, `start`, `end`, `digit` are derived.

```json
{"key": "A", "event": "Spindle", "digit": 0, "counter": 3, "epoch": 7, "start": 195.2, "end": 196.8}
```
`digit` is the event type 0–12 (0 = Artefact, 1–12 = `F1`–`F12`).

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `W` `1` `2` `3` `R` `I` | Score Wake / N1 / N2 / N3 / REM / Inconclusive |
| `Delete` / `Q` | Clear score / toggle uncertain |
| `A`, `F1`–`F12` | Mark drawn region as event; hold + click relabels |
| `Backspace` | Erase events in drawn selection |
| `←` `→` | Previous / next epoch |
| `Z` | Zoom on selection |
| `Ctrl+S` / `Ctrl+C` / `Ctrl+F` | Save / configuration / filter |
| `Ctrl+G` / `Ctrl+N` / `Ctrl+K` | GSSC / NIDRA / MT-KCD |
| `Ctrl+H` | Help |

---

## Code Layout

`scoringhero.py` entry; `ui/` layout; `widgets/` custom widgets; `eeg/` loaders; `scoring/` import/export; `signal_processing/` spectrogram, wavelet, periodogram, SWA; `autoscoring/` GSSC, NIDRA; `event_detection/` detectors; `export/` reports; `config/`, `cache/`, `style/`, `tests/`. Terms in [GLOSSARY.md](GLOSSARY.md). Dependencies in [pyproject.toml](pyproject.toml).

## Contributing

Commit subjects: `[NEW]` feature, `[FIX]` bug fix, `[MOD]` change/refactor, `[DOC]` docs.

## Cite & Support

Cite via *"Cite this repository"* (top right). [Buy me a coffee](https://ko-fi.com/Svennonito) or [sponsor on GitHub](https://github.com/sponsors/SvennoNito).
