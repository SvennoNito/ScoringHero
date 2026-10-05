# SUMO Spindle Detector - Revert Notes

## Status: DISABLED (for later implementation)

The SUMO spindle detector integration has been temporarily disabled pending further debugging and optimization.

## What Was Disabled

The following changes were reverted in the codebase:

1. **ui/setup_ui.py**
   - Commented out SUMO menu item import: `open_sumo_window`
   - Commented out menu action creation for "Spindle Detection (SUMO)"
   - Removed Ctrl+Shift+S shortcut binding

2. **widgets/__init__.py**
   - Commented out SumoWindow export

## What Remains (for later use)

The following SUMO implementation files are preserved in the repository:

- **scoring/sumo_runner.py** - Detection engine with signal preprocessing, model loading, and event extraction
- **scoring/open_sumo_window.py** - Orchestration function for dialog management and result integration
- **widgets/sumoWindow.py** - Settings dialog with channel/marker/threshold selection
- **setup_sumo.py** - Model download and verification utility
- **sumo_lib/** - Official SUMO source code from GitHub
- **SUMO_SETUP.md** - User setup guide
- **SUMO_MODEL_DOWNLOAD.md** - Model download instructions
- **SUMO_IMPLEMENTATION_SUMMARY.md** - Technical implementation details

## Issues Identified

During testing, the following issues were found:

1. **Low Detection Sensitivity**
   - Currently detects ~4-5 spindles per hour instead of expected 30-50+
   - Only 28 events in a 6.4-hour recording

2. **Sparse Probability Output**
   - 99%+ of model probabilities are near 0 or 1 (binary-like)
   - Makes threshold tuning ineffective
   - Even synthetic spindles (12 Hz burst, 100x amplitude) not detected properly

3. **Potential Root Causes**
   - Batch norm statistics may need recalibration
   - Channel interpretation may be inverted
   - Moving average window (42 samples) too aggressive
   - Architecture vs. checkpoint mismatch despite exact state dict match

## Next Steps for Future Implementation

When revisiting SUMO, consider:

1. **Use Official SUMO Library**
   - Instead of custom reimplementation
   - Requires YAML config files (currently missing)
   - More reliable than our architecture interpretation

2. **Debug Batch Normalization**
   - Ensure running_mean and running_var are correct
   - Verify eval() mode is properly set

3. **Investigate Output Interpretation**
   - Test channel 0 vs channel 1 more systematically
   - Try different probability calculation methods
   - Compare with official SUMO prediction code

4. **Signal Preprocessing**
   - Verify resampling to 100 Hz is correct
   - Check z-score normalization assumptions
   - Test with known spindle-containing epochs

## References

- **SUMO Paper**: Kaulen et al. (2022), Sci. Rep. 12, 7686
- **Official GitHub**: https://github.com/dslaborg/sumo
- **MODA Dataset**: https://doi.org/10.1038/s41597-020-0533-4

## Files Modified

- `ui/setup_ui.py` - Commented out SUMO integration
- `widgets/__init__.py` - Commented out SumoWindow import
- `CLAUDE.md` - Already documents SUMO implementation and status

All SUMO implementation files remain intact in the repository for future development.
