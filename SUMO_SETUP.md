# SUMO Spindle Detector Setup & Usage

## Overview

**SUMO** (Slim U-Net trained on MODA) is a deep neural network-based sleep spindle detector integrated into ScoringHero. It detects sleep spindles (brief 0.5–2 second bursts at 11–16 Hz) linked to memory consolidation and other cognitive functions.

**Paper:** Kaulen et al. (2022), *Sci. Rep.* **12**, 7686  
**GitHub:** https://github.com/dslaborg/sumo  
**DOI:** https://doi.org/10.1038/s41598-022-11210-y

## Installation

### 1. Install PyTorch

SUMO requires PyTorch. Choose the appropriate command for your system:

```bash
# Using uv (recommended):
uv pip install torch

# Or use the optional dependency group:
uv sync --extra sumo

# Or with pip:
pip install torch>=2.0.0
```

See https://pytorch.org/get-started/locally/ for version-specific installation instructions.

### 2. Model Download

The SUMO model weights (~100 MB) are needed for spindle detection.

#### Automatic Setup (Recommended)

Run the setup script from the ScoringHero directory:

```bash
python setup_sumo.py
```

This script will:
- Check if the model is already downloaded
- Attempt automatic download from GitHub/HuggingFace
- Provide manual download instructions if needed
- Display the model cache location

#### Manual Download

If automatic download fails, download manually:

**Option 1: GitHub Releases (Recommended)**
1. Visit: https://github.com/dslaborg/sumo/releases
2. Download the latest `sumo_model.pt` file
3. Place it at: `~/.cache/ScoringHero/sumo_model.pt` (or Windows equivalent)

**Option 2: Clone Repository**
```bash
git clone https://github.com/dslaborg/sumo.git
# Copy the model file to ScoringHero cache directory
```

**Option 3: HuggingFace Hub**
```bash
from huggingface_hub import hf_hub_download
hf_hub_download(repo_id='dslaborg/sumo', filename='sumo_model.pt')
```

**Model cache location:**
- **Linux/macOS:** `~/.cache/ScoringHero/sumo_model.pt`
- **Windows:** `C:\Users\[username]\AppData\Local\ScoringHero\ScoringHero\Cache\sumo_model.pt`

## Usage

### 1. Load EEG Data
Open an EEG file (EEGLAB .mat, EDF, etc.) in ScoringHero.

### 2. Run Spindle Detection

**Menu:** Utilities → Spindle Detection (SUMO)  
**Keyboard shortcut:** Ctrl+Shift+S

### 3. Configure Settings

A dialog window will appear with the following options:

#### EEG Channel
Select which channel to analyze (typically a central or vertex channel like Cz, C3, or C4).

#### Event Marker
Choose which annotation slot to save detections to (F1–F12 or A). Default: F2

#### Probability Threshold
Set the confidence threshold (0.0–1.0) for spindle classification:
- **Lower values (e.g., 0.4):** More detections, higher sensitivity, lower specificity
- **Higher values (e.g., 0.7):** Fewer detections, lower sensitivity, higher specificity
- **Default: 0.5**

#### Stage Filter (Optional)
If sleep stages are scored, optionally restrict detections to specific sleep stages.  
**Default:** N2 and N3 only (where spindles are most prominent)

### 4. Review Results

- Detected spindles appear as colored rectangles on the signal trace
- Spindle count is shown in the progress dialog
- All detections are saved to the scoring file
- Results can be exported in standard formats (YASA, Sleeptrip, etc.)

## Technical Details

### Algorithm

1. **Preprocessing**
   - Resample to 100 Hz (if needed)
   - Z-transform (zero mean, unit variance) for normalization

2. **U-Net Inference**
   - 3-level convolutional neural network (16–32 filters)
   - Trained on MODA dataset (180 subjects, expert consensus from 5+ scorers)
   - Runs on CPU (GPU optional for faster processing)

3. **Post-Processing**
   - Moving-average smoothing (0.42 s window)
   - Threshold detection at specified probability
   - Events merged into spindle boundaries

4. **Output**
   - Spindle detections as [start_sec, end_sec] time intervals
   - Added to selected annotation container

### Performance

From Kaulen et al. (2022):

| Metric | Younger (24 y) | Older (62 y) |
|--------|----------------|-------------|
| F1 Score | 0.84 | 0.79 |
| Recall | 0.82 | 0.73 |
| Precision | 0.85 | 0.85 |

SUMO surpasses:
- Previous state-of-the-art algorithms (A7 algorithm: F1=0.74 younger, 0.71 older)
- Average expert scorer (F1=0.76 younger, 0.65 older)
- Other deep learning methods on older populations

## Model File Not Downloading?

If automatic download fails during SUMO spindle detection, see:
**[SUMO Model Download Guide](SUMO_MODEL_DOWNLOAD.md)**

This includes:
- Manual download from GitHub
- How to verify the cache directory
- Troubleshooting steps
- Alternative download sources

## Troubleshooting

### "PyTorch not found" Error

Install PyTorch:
```bash
uv pip install torch
# or
pip install torch
```

### Model Download Fails

1. Check internet connection
2. Try manual download from: https://github.com/dslaborg/sumo/releases
3. Place model at: `~/.cache/ScoringHero/sumo_model.pt`
4. Restart ScoringHero

### Slow Performance

- First run loads the model (~few seconds)
- Subsequent runs use cached model
- GPU acceleration available if torch is compiled with CUDA support

### Unexpected Results

- Verify the selected channel is a valid EEG channel (not reference or artifact marker)
- Check probability threshold (default 0.5 works well for most data)
- Review scored sleep stages—spindles are most prominent in N2/N3
- Compare with expert annotations to validate

## Code Structure

- `widgets/sumoWindow.py` — Settings dialog
- `scoring/sumo_runner.py` — Detection engine (PyTorch model inference)
- `scoring/open_sumo_window.py` — Orchestration (dialog → detection → results)
- Menu action wired in `ui/setup_ui.py`

## Citation

If you use SUMO in your research, please cite:

> Kaulen L, Schwabedal JTC, Schneider J, Ritter P, Bialonski S (2022).  
> Advanced sleep spindle identification with neural networks.  
> *Scientific Reports* **12**, 7686.  
> https://doi.org/10.1038/s41598-022-11210-y

## References

- **MODA Dataset:** Lacourse et al. (2020), *Sci. Data* 7, 190
- **U-Net Architecture:** Ronneberger et al. (2015), MICCAI
- **SUMO GitHub:** https://github.com/dslaborg/sumo
