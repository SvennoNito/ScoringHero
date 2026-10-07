# ScoringHero - The Open-Source Sleep EEG Visualization, Annotation & Scoring Software

Welcome to **ScoringHero**, an open-source project designed to assist you in EEG sleep scoring! After being tested and used by multiple labs for over a year, **ScoringHero** has now reached its beta stage and supports cross-platform compatibility.

![ScoringHero Main Window](screenshots/main.png)

---

## About

**ScoringHero** is an open-source tool for visualizing long-term EEG recordings, marking events (such as sleep spindles, artefacts, or anything really), and performing sleep scoring. It is built with PySide6 (Qt6) and designed for researchers and clinicians who need a fast way for checking and annotating EEG data.

### Quick tour

<table>
  <tr>
    <td width="50%"><img src="screenshots/signal_panel.png" alt="EEG signal panel" /><br /><b>Signal panel</b> — multi-channel EEG with the current stage shown in a movable badge</td>
    <td width="50%"><img src="screenshots/hypnogram_panel.png" alt="Hypnogram with SWA" /><br /><b>Hypnogram</b> — whole-night stages, events and slow-wave activity</td>
  </tr>
  <tr>
    <td width="50%"><img src="screenshots/spectrogram_panel.png" alt="Spectrogram" /><br /><b>Spectrogram</b> — click anywhere to jump to that time</td>
    <td width="50%"><img src="screenshots/periodogram_panel.png" alt="Periodogram" /><br /><b>Periodogram</b> — spectrum of the epoch or of a selected region</td>
  </tr>
  <tr>
    <td width="50%"><img src="screenshots/wavelet_panel.png" alt="Wavelet time-frequency panel" /><br /><b>Time-frequency</b> — Morlet wavelet power of the current epoch</td>
    <td width="50%"><img src="screenshots/events_on_signal.png" alt="Events marked on the signal" /><br /><b>Events</b> — draw, label and relabel events directly on the signal</td>
  </tr>
</table>

---

## Getting Started

### Download the Latest Release

**ScoringHero** is available for **Windows** and **macOS**. For Windows, it is packaged as a standalone executable (`.exe`). For macOS, it comes in versions for older (`x86_64 architecture`) and newer Mac laptops (`arm64 architecture`).

No installation is required. Simply go to the [**Releases**](https://github.com/SvennoNito/ScoringHero/releases) section on the right of this page, download the appropriate file for your operating system, and execute the file to start **ScoringHero**.

### For Mac Users

**ScoringHero** is not registered with Apple (as this would imply a yearly fee). This means you need to manually allow its execution. Follow these steps to run the software:
1. Open Terminal and navigate to your Downloads folder.
2. Run the following command to give execution rights to the software:
   - `chmod +x scoringhero_macOS_arm64` (for ARM64 version)
   - `chmod +x scoringhero_macOS_x86_64` (for x86_64 version)
3. Go to System Preferences > Privacy & Security.
4. Click **Open Anyway** when you see the message: *"scoringhero_macOS_arm64 was blocked to protect your Mac."*

### Running from Source

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.14.3.

```bash
# Clone the repository
git clone https://github.com/SvennoNito/ScoringHero.git
cd ScoringHero

# Install dependencies and run
uv sync
uv run scoringhero.py
```

### Building Standalone Binaries

**Windows:**
```bash
uv sync --extra build-win
./build-win.bat
# Output: dist/scoringhero.exe
```

**macOS** (both architectures, via GitHub Actions on release):
```bash
uv sync --extra build-mac
arch -arm64 ./release-mac.sh   # ARM64
arch -x86_64 ./release-mac.sh  # x86_64
```

---

## Features

### Multi-Channel EEG Signal Display

![EEG signal panel](screenshots/signal_panel.png)

- View multiple EEG channels simultaneously with configurable vertical spacing
- Per-channel amplitude scaling and vertical offset adjustment
- 6 channel colors: Black, Blue, Green, Magenta, Orange, Cyan
- Amplitude reference lines and 1-second grid overlay
- Configurable time axis units: Seconds, Minutes, Hours, or **Clock Time** (set the recording start time in the configuration; the status bar shows the clock time of every epoch)
- **Stack channels** on a shared baseline for overlay comparison
- **Robust z-standardization** (median/IQR normalization) for cross-channel comparison
- Select/deselect all channels or apply settings to all channels at once

<p align="center">
    <img src="screenshots/signal_stacked.png" width="49%" alt="Stacked channels" />
    <img src="screenshots/signal_zscore.png" width="49%" alt="Robustly z-standardized channels" />
</p>

*Left: channels stacked on a shared baseline. Right: robustly z-standardized channels.*

### Stage Badge & Status Bar

![Stage badge for every stage](screenshots/stage_badge.png)

- The **stage badge** shows the stage of the displayed epoch (**Wake**, **N1**, **N2**, **N3**, **REM**, **Inconclusive** or **Unscored**) as a large translucent chip right over the EEG, so you see it while you scan the trace
- **Drag the badge** with the mouse to put it anywhere in the EEG panel; the position is saved with the recording
- Show or hide the badge and change its size in **Configuration → General → Stage in EEG panel**
- When a comparison scoring is loaded and disagrees with yours, the badge reads e.g. *N2 vs N3* and gets a red border

![Status bar](screenshots/status_bar.png)

- The **status bar** shows the epoch (click it, type a number and press Enter to jump), the stage in the same colour as the badge, the confidence, the clock time of the epoch, the EEG file and the scoring file

### Sleep Stage Scoring
- Score epochs as **Wake** (`W`), **N1** (`1`), **N2** (`2`), **N3** (`3`), **REM** (`R`), or **Inconclusive** (`I`)
- Clear a score with `Delete`
- **Confidence flagging**: press `Q` to mark an epoch as uncertain for later review
- Track scoring progress with the epoch readout in the status bar and the stage badge over the EEG
- Automatic save prompt on close if epochs remain unscored

### Compare Scoring

![Compare Scoring Window](screenshots/compare_scoring.png)

![Hypnogram with disagreements highlighted](screenshots/compare_hypnogram.png)

- Load a second scoring file (**Compare → Scoring → Import scoring for comparison**) to compare it against the current scoring
- Epochs where the two scorings disagree are highlighted directly in the hypnogram; the highlighting, the Next disagreement jump and the statistics always follow your latest edits
- A summary statistics window shows agreement metrics (e.g., Cohen's kappa, per-stage agreement) between the two scorings

### Event Annotation
- **13 event types**: Artefact (`A`) + 12 fully customizable events (`F1`–`F12`)
- Label each event type with a custom name (e.g., "Sleep spindle", "K-complex", "Slow wave")
- Assign custom colors from a 13-color palette
- Draw event regions directly on the signal using click-and-drag rectangles
- Real-time display of event duration (seconds) and amplitude while drawing
- Double-click on an existing event to remove it
- Overlapping events of the same type are automatically merged
- Events are displayed on both the signal view and the hypnogram
- **Relabel events**: hold an event key (`A`, `F1`–`F12`) and click on an existing event to reassign it to a different type
- **Erase events in selection**: draw one or more rectangles and press `Backspace` to delete all events inside the drawn region
- **Delete all events**: via the Labels menu — choose to delete all events, events in the current epoch only, or events of a specific type (via the Events config tab)

![Events marked on the signal](screenshots/events_on_signal.png)

<p align="center">
    <img src="screenshots/artefact.png" width="49%" alt="Artefact event marked on signal" />
    <img src="screenshots/arousal.png" width="49%" alt="Arousal event marked on signal" />
</p>

### Smart Navigation
All jumps wrap around from the last epoch to the first. The **Navigation bar** on the left of the window holds one icon-only **Jump button** per kind of epoch; hover a button to see its rule (a disabled button says why it is disabled).

![Navigation bar with a jump button tooltip](screenshots/navigation_bar.png)

| Jump button / Action | Description |
|----------------|-------------|
| **Next unscored** | Jump to the next epoch that hasn't been scored yet |
| **Next uncertain** | Jump to the next **uncertain epoch** (confidence below 0.5) |
| **Next stage transition** | Jump to the next epoch whose stage differs from the current one (unscored counts as a stage) |
| **Next event** | Jump to the next epoch containing a marked event |
| **Next human-scored** | Jump to the next **human-scored epoch** (stage set by you rather than by an autoscorer) |
| **Next disagreement** | Jump to the next epoch where the comparison scoring differs (needs a comparison scoring) |
| **Epoch readout** (status bar) | Click "Epoch 12 / 767" in the status bar, type an epoch number and press Enter to jump there directly |
| **Click on hypnogram** | Navigate to any time point by clicking the hypnogram |
| **Click on spectrogram** | Navigate to any time point by clicking the spectrogram |

### Spectrogram Panel

![Spectrogram panel](screenshots/spectrogram_panel.png)

- Welch power spectral density computed across the full recording
- Configurable frequency range (default: 0–20 Hz)
- Adjustable colorbar power limits (log10 scale)
- Select which channel to display
- Choose the colormap (cividis by default, or viridis, magma or spectral) in the Spectrogram tab of the configuration window; the color bar follows
- Cached computation — no recalculation when navigating epochs

### Hypnogram Panel

![Hypnogram panel](screenshots/hypnogram_panel.png)

Hover the **SWA slider** next to the hypnogram for an explanation of what it does.

- Full-night sleep architecture timeline with color-coded stages
- Current epoch position indicator
- **Slow-wave activity (SWA) overlay** showing delta power across the night
- Adjustable SWA smoothing via a slider with median filter kernel control
- Event markers displayed directly on the hypnogram

### Morlet Wavelet Time-Frequency Panel

![Wavelet time-frequency panel](screenshots/wavelet_panel.png)

- Complex Morlet wavelet decomposition via FFT-based convolution
- Adaptive cycle count per frequency for optimal time-frequency resolution trade-off
- **4 normalization modes:**
  - Raw Power
  - L2-Normalized Power (unit energy wavelets)
  - Z-Standardized Power (zero-mean, unit variance)
  - dB (median baseline) normalization
- Linear or logarithmic frequency scale
- Configurable frequency range (default: 1–45 Hz)
- Extended epoch padding to minimize edge artifacts
- Can be toggled on/off to save screen space
- Choose the colormap (the original spectral map, viridis, magma or cividis) in the Wavelet tab of the configuration window; the color bar follows

### Periodogram Panel

![Periodogram panel](screenshots/periodogram_panel.png)

Hover the **ⓘ** icon in the top right of the panel for a short explanation of what the periodogram shows.

- Welch periodogram of any user-selected EEG region
- Draw a rectangle on the signal to compute the power spectrum of that region
- Configurable frequency band display
- Updates automatically when a selection is drawn or modified

### Signal Filtering

![Filter Window](screenshots/filter.png)

- Apply **high-pass**, **low-pass**, and/or **notch** filters to each EEG channel independently
- Uses a Chebyshev Type 2 filter (zero-phase via forward-backward pass)
- Configurable **cutoff frequency** and **filter order** per channel
- The specified cutoff is the −3 dB point of the displayed signal (high-/low-pass); the notch filter is deepest at the notch frequency and −3 dB at ±1 Hz. Filter order only sets the roll-off steepness
- **Live magnitude response plot** — the frequency response curve updates in real time as you adjust filter parameters
- Filters change the **displayed signal** and therefore also the spectrogram, periodogram and time-frequency power
- **Apply to all channels** checkbox to propagate settings across all channels at once

### Automatic K-Complex & Spindle Detection (MT-KCD)

<p align="center">
    <img src="screenshots/mt_kcd.png" width="49%" alt="MT-KCD window" />
    <img src="screenshots/mt_spindle.png" width="49%" alt="MT-Spindle window" />
</p>

- One-click K-complex and spindle detection via the **MT-KCD algorithm** (multitaper-based) — accessible from the Detectors menu or `Ctrl+K`
- Select which EEG channel to analyse and which event type to store detections in
- Configurable amplitude and slope thresholds and frequency parameters
- Limit detection to specific sleep stages (e.g., N2 only) when a scoring is loaded
- Detections are imported as events and can be reviewed, corrected, and exported like any manually drawn event

### Automatic Sleep Scoring

Automatic sleep stage classifiers live in the **Autoscore** menu. Predicted
stages are imported directly into ScoringHero and can be reviewed, corrected,
and exported like any other scoring.

#### GSSC — scalp EEG/EOG (`Ctrl+G`)

![Auto Score (GSSC) Window](screenshots/GSSC.png)

- One-click automatic sleep scoring via the **Greifswald Sleep Stage Classifier (GSSC)**
- Select which channels to pass as **EEG** and **EOG** inputs (both optional)
- Option to apply GSSC's internal bandpass filter (0.3–30 Hz) before scoring

#### NIDRA — ezscore-f forehead EEG (`Ctrl+N`)

![Auto Score (NIDRA) Window](screenshots/NIDRA.png)

- Artifact-aware **ezscore-f** classifiers for **two-channel forehead EEG** (ZMax,
  DCM, CGX PatchEEG and comparable montages), from
  [Coon et al. 2025](https://doi.org/10.1101/2025.06.02.657451), run from the
  ONNX exports [NIDRA](https://github.com/paulzerr/nidra) publishes — inside
  ScoringHero, no second Python environment
- Select the **left** and **right** forehead derivation, and one of two model
  variants (`ez6`, `ez6moe` mixture of experts). Weights are downloaded on
  first use
- A sixth **artifact** class keeps unusable epochs out of the sleep statistics:
  they are left unscored (or scored *Inconclusive*), flagged as unclean, and can
  be marked with an event marker
- Optionally stores the per-epoch class probabilities (hypnodensity) in the
  scoring file and shows a summary figure (hypnodensity + hypnogram) when
  finished
- Needs `onnxruntime` and `mne` (`uv sync --extra nidra`). See
  [NIDRA_SETUP.md](NIDRA_SETUP.md)

![NIDRA summary figure: hypnodensity and hypnogram](screenshots/summary_image.png)

### Sleep Report (PDF Export)

- Generate a multi-page PDF sleep report via **File → Export Report → Sleep Report**
- The report includes:
  - Hypnogram with stage-specific colors
  - Whole-night spectrogram (using cached Welch data)
  - Example EEG trace with channel headers
  - Sleep statistics: TST, TRT, sleep efficiency, and stage distribution (epochs scored *Inconclusive* count as neither sleep nor wake, but are part of the scored-epoch total)
  - Sleep latencies: time to first N2/N3 and REM latency

<p align="center">
    <img src="screenshots/report_options.png" width="32%" alt="Sleep report options" />
    <img src="screenshots/report_page.png" width="60%" alt="Sleep report page" />
</p>

### Zoom
- Draw a rectangle on the signal and press `Z` to zoom into that region
- Inspect fine-grained signal details at any scale

![Zoom on a selected region](screenshots/zoom.png)

---

## Menus

<table>
  <tr>
    <td><img src="screenshots/menu_file.png" alt="File menu" /><br /><b>File</b></td>
    <td><img src="screenshots/menu_stages.png" alt="Stages menu" /><br /><b>Stages</b></td>
    <td><img src="screenshots/menu_events.png" alt="Events menu" /><br /><b>Events</b></td>
  </tr>
  <tr>
    <td><img src="screenshots/menu_autoscore.png" alt="Autoscore menu" /><br /><b>Autoscore</b></td>
    <td><img src="screenshots/menu_detectors.png" alt="Detectors menu" /><br /><b>Detectors</b></td>
    <td><img src="screenshots/menu_utilities.png" alt="Utilities menu" /><br /><b>Utilities</b></td>
  </tr>
  <tr>
    <td><img src="screenshots/menu_compare.png" alt="Compare menu" /><br /><b>Compare</b></td>
    <td><img src="screenshots/menu_configuration.png" alt="Configuration menu" /><br /><b>Configuration</b></td>
    <td><img src="screenshots/menu_help.png" alt="Help menu" /><br /><b>Help</b></td>
  </tr>
</table>

---

## Supported File Formats

### EEG Data Import

| Format | Extension | Notes |
|--------|-----------|-------|
| EEGLAB | `.mat` | MATLAB v5 and v7.3+ (HDF5). Reads `EEG.data`, `EEG.srate`, and `EEG.chanlocs` |
| EDF | `.edf` | European Data Format, read via pyedflib |
| EDF (Volt-scaled) | `.edf` | For EDF files recorded in Volts — auto-converts to µV |
| Zurich R09 | `.r09` | Legacy format support |

#### EEGLAB `.mat` — Required Structure

ScoringHero expects the file to contain a top-level `EEG` struct with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `EEG.data` | numeric array `(n_channels × n_samples)` | Raw EEG signal (µV typical, any unit accepted) |
| `EEG.srate` | scalar | Sampling rate in Hz |
| `EEG.chanlocs` | struct array | Channel metadata — only the `labels` field is read |
| `EEG.chanlocs(i).labels` | string | Channel name for channel `i` |

Both **MATLAB v7 and earlier** (via `scipy.io.loadmat`) and **MATLAB v7.3+ / HDF5** (via `h5py`) are supported. The loader auto-detects which format applies.

Robustness notes:
- If `data` is stored transposed `(n_samples × n_channels)`, it is automatically corrected.
- If `chanlocs` is missing or has the wrong number of entries, names fall back to `CH1, CH2, …, CHn` with a console warning.

**Minimal working example (MATLAB):**
```matlab
EEG.data              = randn(2, 125 * 30 * 100);  % 2 channels, 100 × 30 s epochs @ 125 Hz
EEG.srate             = 125;
EEG.chanlocs(1).labels = 'C3-A2';
EEG.chanlocs(2).labels = 'C4-A1';
save('myrecording.mat', 'EEG', '-v7.3');            % -v7.3 required for files > 2 GB
```

#### EDF (`.edf`)

Standard European Data Format, loaded with pyedflib (`pyedflib.EdfReader`). No special structure beyond a valid EDF file. A second loader variant auto-converts Volt-scaled signals to µV.

#### Zurich R09 (`.r09`)

Legacy binary format. Fixed 9-channel layout at 128 Hz with hardcoded channel names: `F3-A2, F4-A1, C3-A2, C4-A1, O1-A2, O2-A1, EOG1, EOG2, EMG`. Samples stored as `int16`.

---

### Scoring Import

| Format | Extension | Source | Notes |
|--------|-----------|--------|-------|
| ScoringHero | `.json` | Native | Full stages + events + confidence |
| YASA | `.txt` | Yet Another Spindle Algorithm | One stage per line |
| Sleeptrip | `.csv` | MATLAB Sleeptrip toolbox | Single column, numeric encoding |
| Sleepyland | `.annot` | Sleepyland | Includes per-stage confidence scores |
| GSSC | `.csv` | Greifswald Sleep Stage Classifier | Includes per-stage confidence |
| Zurich VIS | `.vis` | Zurich scoring format | 20-second epoch standard |

Every format goes through the same checks when a scoring file is opened or imported for comparison:

- **More epochs than the recording**: exactly one extra epoch is dropped with a warning; two or more extra epochs ask whether to cancel or truncate.
- **Fewer epochs than the recording**: exactly one missing epoch is filled by copying the last epoch, with a warning; two or more missing epochs ask whether to cancel or copy the last epoch until the length matches. Copied epochs keep the stage, source and confidence of the epoch they were copied from.
- **Unknown stage names or codes**: a warning asks whether to cancel or replace them with *unscored*.
- **Cancel** aborts a comparison import. When opening a recording, cancelling on its own ScoringHero file opens the recording with an empty scoring; the file on disk stays untouched until your first edit, so you can fix the epoch length setting and reopen.

#### YASA (`.txt`)

Plain text, one stage label per line (one line = one epoch). Lines that do not match a known token are skipped.

| Accepted token(s) | Stage |
|-------------------|-------|
| `W`, `WAKE` | Wake |
| `N1`, `NREM1`, `1` | N1 |
| `N2`, `NREM2`, `2` | N2 |
| `N3`, `NREM3`, `3` | N3 |
| `R`, `REM`, `Rem`, `4` | REM |

#### Sleeptrip (`.csv`)

CSV with one numeric code per row (first column used, header optional).

| Value | Stage |
|-------|-------|
| `0` | Wake |
| `1` | N1 |
| `2` | N2 |
| `3` | N3 |
| `5` | REM |

#### SleepyLand (`.annot`)

Tab-separated file with a header row. Column 1 contains the stage label (`W`, `N1`, `N2`, `N3`, `R`). Column 5 (meta) contains semicolon-separated probabilities used as confidence:

```
pW=0.10;pN1=0.05;pN2=0.75;pN3=0.08;pR=0.02
```

#### GSSC (`.csv`)

CSV with header: `Epoch, Time, Stage, Conf_W, Conf_N1, Conf_N2, Conf_N3, Conf_R`.

| Stage value | Stage |
|-------------|-------|
| `0` | Wake |
| `1` | N1 |
| `2` | N2 |
| `3` | N3 |
| `4` | REM |

#### Zurich VIS (`.vis`)

Space-separated text. First line is an epoch offset (usually `0`). Each subsequent line: `<epoch_number> <stage_code> [optional comment]`.

| Code | Stage |
|------|-------|
| `0` | Wake |
| `1` | N1 |
| `2` | N2 |
| `3` | N3 |
| `r` | REM |
| `e` | End marker — replaced by the previous epoch's stage |

Default epoch length assumed: 20 s. Missing epochs are forward-filled.

---

### Scoring Export & Native JSON Format

ScoringHero saves scoring to `{filename}.json` next to the EEG file. The file is a JSON array with exactly two elements:

```
[ <stages>, <annotations> ]
```

**Element 0 — stages:** one dict per epoch:

```json
{
  "epoch":      1,       // 1-indexed epoch number
  "start":      0,       // epoch start time in seconds
  "end":        30,      // epoch end time in seconds
  "stage":      "N2",    // human-readable label (see encoding table)
  "digit":      -2,      // numeric code (see encoding table)
  "confidence": 0.85,    // model confidence 0–1, or null
  "channels":   ["C3"],  // channels displayed when the epoch was scored
  "clean":      1,       // 1 = clean, 0 = artifact
  "source":     "YASA"   // originating tool, or null
}
```

**Stage encoding** (on load the `stage` name wins; `digit`, `epoch`, `start` and `end` are derived and ignored):

| `stage` | `digit` |
|---------|:-------:|
| `"Wake"` | `1` |
| `"N1"` | `-1` |
| `"N2"` | `-2` |
| `"N3"` | `-3` |
| `"REM"` | `0` |
| `"Inconclusive"` | `2` |
| `null` (unscored) | `null` |

**Element 1 — annotations:** one dict per marked event:

```json
{
  "key":     "A",      // shortcut key assigned to this event type
  "event":   "Spindle", // human-readable event label
  "digit":   0,         // annotation type index (0–12; 0 = Artefact, 1–12 = F1–F12)
  "counter": 3,         // sequential index within this event type
  "epoch":   7,         // epoch where the event occurs
  "start":   195.2,     // absolute start time in seconds
  "end":     196.8      // absolute end time in seconds
}
```

Up to 13 annotation types are supported (indices 0–12).

---

## Keyboard Shortcuts

### Sleep Stage Scoring

| Key | Action |
|-----|--------|
| `W` | Score as Wake |
| `1` | Score as N1 |
| `2` | Score as N2 |
| `3` | Score as N3 |
| `R` | Score as REM |
| `I` | Score as Inconclusive |
| `Delete` | Remove score (set to None) |
| `Q` | Toggle "Not sure" confidence flag |

### Event Marking

| Key | Action |
|-----|--------|
| `A` | Mark drawn region as Artefact |
| `F1`–`F12` | Mark drawn region as Event 1–12 (labels customizable in config) |
| Hold `A`/`F1`–`F12` + click | Relabel an existing event to that type |
| `Backspace` | Erase all events inside the drawn selection |

### Navigation & Tools

| Key | Action |
|-----|--------|
| `→` | Next epoch |
| `←` | Previous epoch |
| `Z` | Zoom on selected EEG region |
| `Ctrl+S` | Save scoring |
| `Ctrl+C` | Open configuration window |
| `Ctrl+F` | Open filter window |
| `Ctrl+G` | Open Auto Score (GSSC) window |
| `Ctrl+N` | Open Auto Score (NIDRA, ezscore-f) window |
| `Ctrl+K` | Open K-Complex Detection (MT-KCD) window |
| `Ctrl+H` | Show help |

---

## Configuration

Open the configuration window with `Ctrl+C`. Settings are saved per-file as `{filename}.config.json` alongside the EEG data.

### General Tab

![Configuration Window — General Tab](screenshots/general_config.png)
- Sampling rate (Hz)
- Epoch length (seconds)
- Distance between channels (µV)
- Reference amplitude line (µV)
- Extension epoch duration for wavelet edge-artifact handling
- Periodogram frequency limits
- EEG panel time unit (Seconds / Minutes / Hours / Clock Time)
- Recording start time (always editable; sets the clock time shown in the status bar and on the time axes)
- Stage in EEG panel: show or hide the stage badge and set its size (drag it in the EEG panel to move it)

### Channels Tab

![Configuration Window — Channels Tab](screenshots/channel_config.png)

- Per-channel: name, visibility toggle, color, scaling factor (%), vertical shift (µV)
- Apply changes to all channels at once
- Select / deselect all channels
- Stack channels on the same baseline
- Robust z-standardize channels

### Events Tab

![Configuration Window — Events Tab](screenshots/event_config.png)
- Custom label for each of the 12 event types
- Custom color assignment from a 13-color palette
- Displays event count and total duration per event type
- Per-type delete button to remove all events of that type

### Spectrogram Tab

![Configuration Window — Spectrogram Tab](screenshots/spectrogram_config.png)

- Channel selection for spectrogram computation
- Frequency display limits (Hz)
- Colorbar power limits

### Periodogram Tab

![Configuration Window — Periodogram Tab](screenshots/periodogram_config.png)

- Channel selection for the periodogram
- Frequency display limits (Hz)
- Display mode: 1/f Removed, dB or Raw Power

### Wavelet Tab

![Configuration Window — Wavelet Tab](screenshots/wavelet_config.png)

- Channel selection for wavelet computation
- Frequency scale: Linear or Logarithmic
- Frequency display limits (Hz)
- Normalization mode: Raw Power, L2-Normalized, Z-Standardized, or dB (median baseline)
- Per-mode colorbar power limits
- Toggle wavelet panel visibility

---

## Signal Processing Details

### Spectrogram
- Welch method: 4-second Hann window, 2-second hop, constant detrending
- Power displayed on log10 scale with Cividis colormap
- Computed once and cached for the session

### Morlet Wavelet Time-Frequency
- FFT-based convolution with complex Morlet wavelets
- Adaptive `n_cycles` per frequency: ranges from 3 (low frequencies) to `freq/2` (high frequencies)
- Extended epoch signal used to avoid edge artifacts
- Results cached per channel and settings

### Periodogram
- Welch periodogram of the signal within a user-drawn rectangle
- Min-max scaled to [0, 1] for display
- Trimmable to a frequency band of interest

### Slow-Wave Activity
- Delta band (0.5–4 Hz) power per epoch
- Displayed as an overlay on the hypnogram
- Smoothing controlled by a slider (median filter with adjustable kernel)

---

## Architecture

```
scoringhero.py              Main entry point and window
├── ui/setup_ui.py          Widget layout and signal/slot wiring
├── widgets/                PySide6 custom widgets
│   ├── signal_widget       Multi-channel EEG signal display
│   ├── spectogram_widget   Welch spectrogram panel
│   ├── hypnogram_widget    Sleep stage timeline
│   ├── tf_widget           Morlet wavelet time-frequency
│   └── ...                 Slider, periodogram, paint overlay, etc.
├── eeg/                    EEG file loaders (EEGLAB, EDF, R09)
├── scoring/                Scoring import/export (6 formats)
├── signal_processing/      Spectrogram, Morlet TF, periodogram, SWA
├── events/                 Event annotation handling
├── config/                 Configuration window and settings I/O
├── mouse_click/            Click handlers for hypnogram/spectrogram
├── paint_event/            Event rectangle drawing overlay
├── utilities/              GUI state (refresh, redraw, zoom, navigation)
├── cache/                  Computed data caching
├── style/                  Modern light theme (QSS), icons, plot style
└── help/                   Help content and images
```

---

## Dependencies

Key libraries:
- **PySide6** — Qt6 Python bindings (GUI framework)
- **NumPy** / **SciPy** — Numerical computing and signal processing
- **Matplotlib** — Plotting backend for signal and spectral displays
- **pyedflib** — EDF file reading
- **h5py** — HDF5 support for MATLAB v7.3+ files
- **PyQtGraph** — Fast interactive plotting
- **PyWavelets** — Wavelet transforms

See [pyproject.toml](pyproject.toml) for the full dependency list and [uv.lock](uv.lock) for pinned versions.

---

## Contributing

Contributions are welcome! Please follow the existing commit convention:
- `[NEW]` — New feature or capability
- `[FIX]` — Bug fix
- `[ADD]` — Enhancement to existing feature
- `[MOD]` — Code modification or refactoring

---

## How to Cite

If you use **ScoringHero** in your work, please cite this software using the metadata found under *"Cite this repository"* on the top right of this page.

---

## Support the Project

[Buy me a coffee](https://ko-fi.com/Svennonito) or [sponsor me on GitHub](https://github.com/sponsors/SvennoNito) to help keep updates coming!
Every little bit fuels late-night coding sessions — thanks for being awesome!
