# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ScoringHero** is an open-source GUI application for sleep EEG scoring and visualization. Built with PySide6 (Qt), it allows users to:
- Load and visualize long-term EEG recordings (EEGLAB, EDF formats)
- Mark events (sleep spindles, artifacts, etc.) interactively
- Score sleep stages (W, N1, N2, N3, REM, Inconclusive)
- Import/export scoring from various formats (YASA, Sleeptrip, SleepyLand, GSSC, VIS)
- View spectrograms, hypnograms, and time-frequency representations

## Running the Application

### Development Mode
```bash
# Install uv (one-time): https://docs.astral.sh/uv/getting-started/installation/

# Setup and run
uv sync                    # Creates .venv and installs all deps
uv run scoringhero.py      # Run the application

# Or activate manually
./.venv/Scripts/activate   # Windows
source ./.venv/bin/activate  # macOS/Linux
python scoringhero.py
```
- Starts with example data from `example_data/example_data.mat` (`devmode=1` in `Ui_MainWindow.__init__`) when self.devmode = 1 in scoringhero.py
- Version displayed in window title

### Building Standalone Binaries

**macOS** (via GitHub Actions on release):
```bash
uv venv .venv_arm64
uv sync --extra build-mac
arch -arm64 ./release-mac.sh
```
Builds for both arm64 and x86_64 architectures.

**Windows/Other**:
```bash
uv sync --extra build-win
uv run pyinstaller scoringhero.spec
```
Generates `dist/scoringhero.exe`. The spec file bundles:
- MNE library data (required for channel location info)
- Style assets (`style/modern_theme.qss`)
- Help images (`help/images/selection_box.png`)

## Architecture Overview

The application follows a modular architecture with specialized components:

```
scoringhero.py (main entry point)
├── ui/setup_ui.py         → Wires all widgets and signal/slot connections
├── widgets/               → PySide6 custom widgets (main UI components)
├── eeg/                   → EEG file loading (EEGLAB, EDF, R09)
├── scoring/               → Scoring import/export (multiple formats)
├── signal_processing/     → DSP: spectrograms, Morlet TF, periodogram
├── events/                → Event annotations and interactions
├── utilities/             → GUI state management and helpers
├── cache/                 → Caching computed data (spectrograms, etc.)
├── config/                → Configuration window and settings
├── mouse_click/           → Click handlers (hypnogram, spectrogram, sliders)
├── paint_event/           → Custom painting for event visualization
├── help/                  → Help text and images
└── style/                 → QSS theming
```

### Configuration Panel

Scoringhero allows to configure certain parameters. Those parameters are then saved in a `config.json` file. During development, when changing the options inside this file, `check_for_compatibility.py` needs to be updated such that previous `config.json` files still work. The default value must be added to those older files then.

## Key Modules

### Widgets (`widgets/`)
The main visual components of the UI:
- **SignalWidget**: Raw EEG signal display (matplotlib embedded in Qt)
- **SpectogramWidget**: Time-frequency spectrogram view
- **HypnogramWidget**: Sleep stage timeline visualization
- **TfWidget**: Morlet time-frequency representation
- **ConfigurationWindow**: Settings panel for display and analysis parameters
- **AnnotationContainer**: Event marker storage and display

### EEG Loading (`eeg/`)
Loaders for different EEG formats. Each has a `load_*` function that populates `ui.data`:
- **load_eeglab.py**: MATLAB EEGLAB `.mat` files (primary format)
- **load_edf.py**: EDF format (both standard and voltage-scaled variants)
- **load_r09.py**: R09 format (legacy)
- **load_wrapper.py**: Dispatcher that auto-detects format and calls appropriate loader

### Signal Processing (`signal_processing/`)
Computation of spectral and time-frequency representations:
- **compute_morlet_tf.py**: Morlet wavelet time-frequency decomposition
- **compute_spectogram.py**: STFT-based spectrogram
- **compute_periodogram.py**: Welch periodogram (for frequency bands)
- **compute_swa.py**: Slow-wave activity computation

All results are cached in the `cache/` directory to avoid recomputation.

### Scoring (`scoring/`)
Import and export of sleep stage scorings from various software:
- **load_yasa.py**, **load_sleeptrip.py**, **load_sleepyland.py**, **load_gssc.py**, **load_vis.py**: Import from different scoring systems
- **write_scoring.py**: Export to ScoringHero JSON format
- **scoring_import_window.py** & **scoring_export_window.py**: UI dialogs

### Event System (`events/`, `mouse_click/`, `paint_event/`)
- **event_handler.py**: Main event dispatcher
- **draw_event_in_this_epoch.py**: Renders event markers on the EEG signal
- **click_on_hypnogram.py**, **click_on_spectogram.py**: Handle user clicks and update state
- **paint_event_handler.py**: Custom painting for event visualization

### GUI State Management (`utilities/`)
- **refresh_gui.py**: Update all widgets after epoch change or scoring update
- **redraw_gui.py**: Low-level redraw of specific components
- **zoom_on_selected_eeg.py**: Pan and zoom on the signal display
- **score_stage.py**: Record a sleep stage score
- **next_epoch.py**, **prev_epoch.py**: Navigate epochs (also triggered by arrow keys)

## Data Flow

1. **Load EEG**: User selects file → `load_wrapper` detects format → calls loader → populates `ui.data` (dict)
2. **Display**: `refresh_gui` updates all widgets from current epoch data
3. **Interact**: User clicks on hypnogram/spectrogram or presses keys
   - Handlers call `score_stage`, `next_epoch`, etc.
   - These update `ui.stages` (list of stage dicts with keys like `"digit"`, `"event"`)
   - Call `refresh_gui` to redraw everything
4. **Save**: On exit or manual save → `write_scoring` exports `ui.stages` to JSON

## Important State Variables

In `Ui_MainWindow`:
- **`this_epoch`** (int): Currently displayed epoch index
- **`data`** (dict): Loaded EEG data (keys: `times`, `signal`, `sfreq`, etc.)
- **`stages`** (list): Sleep stage scores, one dict per epoch
- **`AnnotationContainer`** (list of objects): Event annotations for each channel
- **`filename`** (str): Path to loaded EEG file (stem, no extension)
- **`version`** (list): [major, minor, patch] version numbers
- **`app_path`** (str): Root directory (for accessing resources)

## Development Notes

### Version Management
- Version is hard-coded in `scoringhero.py:40` as `self.ui.version = [0, 1, 3]`
- Update this before releases and document in commits

### Commit Convention
Commits follow a structured format (seen in git log):
- `[NEW]` - New feature or capability
- `[FIX]` - Bug fix
- `[ADD]` - Enhancement to existing feature
- `[MOD]` - Code modification or refactoring

### Threading and Performance
- Heavy computations (spectrograms, Morlet TF) are cached to avoid recalculation
- Some operations use `@timing_decorator` to log performance
- No multi-threading currently; all work on main Qt thread

### Styling
- Modern dark theme via `style/modern_theme.qss`
- Applied at startup in `apply_app_theme()`
- PySide6 QSS follows CSS-like syntax

## Common Development Tasks

**Add a new EEG format loader:**
1. Create `eeg/load_myformat.py` with `load_myformat(filename, ui)` function
2. Update `eeg/load_wrapper.py` to detect and call your loader
3. Loader must populate `ui.data` dict with: `times`, `signal` (n_channels × n_samples), `sfreq`

**Add a new scoring import format:**
1. Create `scoring/load_myformat.py` with loader function
2. Add to dropdown in `scoring/scoring_import_window.py`
3. Return list of stage dicts matching ScoringHero format

**Modify the UI layout:**
- See `ui/setup_ui.py` for the grid layout structure
- Widgets are added to `ui` object; connect signals/slots with `connect()`

**Debug GUI rendering:**
- Use `utilities/refresh_gui.py` to update displays
- Check `utilities/redraw_gui.py` for low-level redraw logic
- Add print statements or use Qt's built-in inspector
