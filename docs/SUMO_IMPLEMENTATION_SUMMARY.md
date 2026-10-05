# SUMO Spindle Detector - Implementation Summary

## Status: COMPLETE & READY TO USE ✓

The SUMO (Slim U-Net trained on MODA) deep learning spindle detector has been successfully integrated into ScoringHero.

## What Was Implemented

### New Files Created:
1. **widgets/sumoWindow.py** (180 lines) — Settings dialog with:
   - Channel selection
   - Event marker selection
   - Probability threshold adjustment (0.0–1.0)
   - Optional sleep stage filtering
   - Info tooltips explaining the algorithm

2. **scoring/sumo_runner.py** (350+ lines) — Detection engine with:
   - PyTorch inference on CPU
   - Signal preprocessing (resampling, z-transformation)
   - Model loading from checkpoint (.ckpt format)
   - Moving-average post-processing
   - Event extraction and boundary detection

3. **scoring/open_sumo_window.py** (95 lines) — Orchestration:
   - Dialog management
   - Progress feedback
   - Stage filtering
   - Result integration into annotation system
   - Error handling with helpful messages

4. **setup_sumo.py** (150 lines) — Setup utility:
   - Checks for existing model
   - Attempts automatic download
   - Provides manual download instructions
   - Verifies installation

5. **sumo_lib/** — Official SUMO source code
   - Complete U-Net implementation
   - Config system
   - Model training & evaluation code
   - Integrated from official GitHub repository

### Files Modified:
- **ui/setup_ui.py** — Added menu action "Spindle Detection (SUMO)" [Ctrl+Shift+S]
- **widgets/__init__.py** — Exported SumoWindow class
- **pyproject.toml** — Added torch as optional dependency
- **CLAUDE.md** — Documented SUMO implementation

### Documentation Created:
- **SUMO_SETUP.md** — User setup & usage guide
- **SUMO_MODEL_DOWNLOAD.md** — Detailed model download instructions
- **SUMO_IMPLEMENTATION_SUMMARY.md** — This file

## How to Use

### 1. First Time Setup

Run the setup script:
```bash
python setup_sumo.py
```

Or manually install PyTorch:
```bash
uv pip install torch
# or
uv sync --extra sumo
```

The model (310 KB checkpoint) is auto-cached on first use.

### 2. In ScoringHero

1. **Load EEG data** (any format: .mat, .edf, etc.)
2. **Open detector**: Menu → Utilities → **Spindle Detection (SUMO)** [Ctrl+Shift+S]
3. **Configure**:
   - Select EEG channel (Cz, C3, C4, etc.)
   - Choose event marker (F1–F12, default F2)
   - Set probability threshold (0.5 default works well)
   - Optionally filter to N2/N3 sleep stages
4. **Run**: Click OK
5. **Results**: Detected spindles appear as colored rectangles on signal

## Technical Details

### Model
- **Architecture**: Slim U-Net (3 levels, 16–32 filters)
- **Training data**: MODA dataset (180 subjects, 5+ expert consensus annotations)
- **Input**: Single-channel EEG at 100 Hz
- **Output**: Probability map → spindle events
- **Format**: PyTorch Lightning checkpoint (`sumo_model.ckpt`)
- **Size**: 310 KB (compressed)
- **GPU**: Optional (CPU-only by default)

### Performance (from paper)
| Metric | Younger | Older |
|--------|---------|-------|
| F1 Score | 0.84 | 0.79 |
| Recall | 0.82 | 0.73 |
| Precision | 0.85 | 0.85 |

**Surpasses**: A7 algorithm (F1: 0.74/0.71), average expert (F1: 0.76/0.65)

### Processing
1. **Preprocess**: Resample to 100 Hz, z-transform
2. **Infer**: U-Net processes signal → probability map
3. **Post-process**: Moving-average smooth (0.42 s window)
4. **Threshold**: Extract events above probability threshold
5. **Output**: [start_sec, end_sec] per spindle

## System Integration

### Menu
- Location: Utilities menu (next to K-Complex Detection)
- Shortcut: Ctrl+Shift+S
- Wired in: `ui/setup_ui.py`

### Annotation System
- Detected spindles → Annotation containers (F1–F12 or A)
- Automatically saved to scoring file
- Exportable in all formats (YASA, Sleeptrip, etc.)

### Error Handling
- **PyTorch not found**: Clear message with install instructions
- **Model not cached**: Attempts auto-download, provides manual instructions
- **Detection fails**: Friendly error with diagnostic info

## Model Cache Location

- **Windows**: `C:\Users\[user]\AppData\Local\ScoringHero\ScoringHero\Cache\sumo_model.ckpt`
- **Linux/macOS**: `~/.cache/ScoringHero/sumo_model.ckpt`

Verify with:
```bash
python setup_sumo.py
```

## Dependencies

### Required
- PyTorch: `torch>=2.0.0`
- Standard: NumPy, SciPy, PySide6 (already in ScoringHero)

### Optional
- appdirs: For cross-platform cache directory (auto-falls back to ~/.cache)
- GPU support: Install CUDA-enabled torch (optional)

### Installation
```bash
# All-in-one with optional deps
uv sync --extra sumo

# Or just PyTorch
uv pip install torch
```

## Testing

The implementation was tested with:
- ✓ Import verification (all modules load correctly)
- ✓ Model loading (PyTorch Lightning checkpoint loads successfully)
- ✓ Inference (detection runs on test signals)
- ✓ UI integration (dialog opens, settings accepted)
- ✓ Error handling (graceful fallbacks for missing dependencies)

## Citation

If you use SUMO in your research, cite:

> Kaulen L, Schwabedal JTC, Schneider J, Ritter P, Bialonski S (2022).
> Advanced sleep spindle identification with neural networks.
> *Scientific Reports* **12**, 7686.
> https://doi.org/10.1038/s41598-022-11210-y

## References

- **GitHub**: https://github.com/dslaborg/sumo
- **Paper**: https://doi.org/10.1038/s41598-022-11210-y
- **MODA Dataset**: https://doi.org/10.1038/s41597-020-0533-4
- **PyTorch**: https://pytorch.org/

## Future Enhancements

Possible improvements (not implemented):
- [ ] Batch processing multiple channels simultaneously
- [ ] GPU acceleration wrapper
- [ ] Fine-tuning on project-specific data
- [ ] Custom probability thresholds per age group
- [ ] Integration with other event detectors (e.g., K-complexes + spindles)
- [ ] Real-time streaming inference for long recordings

## Troubleshooting

### Model download fails
→ See [SUMO_MODEL_DOWNLOAD.md](SUMO_MODEL_DOWNLOAD.md)

### PyTorch not found
→ `uv pip install torch` or `uv sync --extra sumo`

### Slow first run
→ Normal (model loads from disk). Subsequent runs are fast.

### Detection quality
→ Adjust probability threshold (lower = more sensitive, higher = specific)
→ Ensure data is properly preprocessed (no extreme artifacts)

## Support

- **SUMO issues**: https://github.com/dslaborg/sumo/issues
- **ScoringHero issues**: https://github.com/rkoushik535/ScoringHero/issues
- **Documentation**: See SUMO_SETUP.md
