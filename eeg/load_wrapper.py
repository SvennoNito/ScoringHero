import os
import numpy as np
from config.write_configuration import write_configuration
from config.load_configuration import load_configuration
from scoring.load_scoring import load_scoring
from scoring.events_to_ui import events_to_ui
from .load_eeglab import load_eeglab
from .load_r09 import load_r09
from .load_edf import load_edf
from .number_of_epochs import number_of_epochs
from signal_processing.times_vector import times_vector
from utilities.apply_tf_visibility import apply_tf_visibility
from utilities.refresh_gui import _update_export_menu_state
from utilities.busy_indicator import run_busy
from utilities.overlay_state import drop_overlay_signal
from .displayed_signal import settings_changed


def load_single(filename_prefix, datatype):
    """Load a single EEG file and return (eeg_data, srate, channel_names, units).

    All signals are at the common (highest native) sampling rate srate.
    """
    if datatype == "eeglab":
        return load_eeglab(filename_prefix)
    if datatype == "r09":
        return load_r09(filename_prefix)
    if datatype == "edf":
        return load_edf(filename_prefix)
    if datatype == "edfvolt":
        return load_edf(filename_prefix, scale_to_uv=True)


def _repair_stored_sampling_rate(ui, srate):
    """A recording saved by an older loader may store a different sampling rate than
    the loader now reports. Refresh the stored rate (other settings are kept); the
    cached derived data no longer matches its inputs and is rebuilt."""
    if ui.config[0]["Sampling_rate_hz"] == srate:
        return
    ui.config[0]["Sampling_rate_hz"] = srate
    write_configuration(f"{ui.filename}.config.json", ui.config)


def _reset_for_new_recording(ui):
    ui.this_epoch = 0

    # A newly loaded primary recording invalidates any loaded overlay signal
    # (different duration/channels), so drop it and reset the related menu state.
    drop_overlay_signal(ui)
    ui.eeg_data_display_ref = None

    # Reset filter window so it is recreated with the new channel configuration
    ui.FilterWindow = None


def load_wrapper(ui, datatype, extra_files=None):
    """Load at startup: reading the files blocks, building the displayed signal and
    the analysis data runs under the busy indicator."""
    _reset_for_new_recording(ui)
    events = _load_heavy(ui, datatype, extra_files)
    _show_loaded(ui, events)


def load_wrapper_busy(ui, datatype, extra_files, on_done, on_error):
    """Load with the heavy step off the GUI thread and a busy indicator on top."""
    _reset_for_new_recording(ui)
    run_busy(ui, "Loading recording…",
             lambda: _load_heavy(ui, datatype, extra_files),
             lambda events: _show_loaded(ui, events, on_done), on_error)


def _load_heavy(ui, datatype, extra_files):
    """Pure-compute half of loading (no GUI objects). Returns the scoring events."""
    ui.eeg_data, srate, channel_names, units = load_single(ui.filename, datatype)

    if extra_files:
        for filepath in extra_files:
            prefix, _ = os.path.splitext(filepath)
            extra_data, extra_srate, extra_channel_names, extra_units = load_single(prefix, datatype)
            if extra_srate != srate:
                raise ValueError(
                    f"Sampling rate mismatch: primary file has {srate} Hz, "
                    f"but '{os.path.basename(filepath)}' has {extra_srate} Hz."
                )
            if extra_data.shape[1] != ui.eeg_data.shape[1]:
                raise ValueError(
                    f"Sample count mismatch: primary file has {ui.eeg_data.shape[1]} samples, "
                    f"but '{os.path.basename(filepath)}' has {extra_data.shape[1]} samples. "
                    f"All files must have the same number of samples."
                )
            ui.eeg_data = np.vstack([ui.eeg_data, extra_data])
            channel_names = channel_names + extra_channel_names
            units = units + extra_units

    try:
        numchans = ui.eeg_data.shape[0]
    except:
        numchans = 6

    # Raw data stays in file order; each channel shows the file signal at its Signal_index
    ui.signal_names = channel_names
    ui.config = load_configuration(f"{ui.filename}.config.json", numchans, srate, channel_names, ui.app_path, units=units)
    _repair_stored_sampling_rate(ui, srate)

    ui.numepo = number_of_epochs(
        ui.eeg_data.shape[1],
        ui.config[0]["Sampling_rate_hz"],
        ui.config[0]["Epoch_length_s"],
    )
    ui.stages, events = load_scoring(
        f"{ui.filename}.json", ui.config[0]["Epoch_length_s"], ui.numepo, "scoringhero"
    )

    times_vector(ui)
    return events


def _show_loaded(ui, events, on_done=None):
    """GUI-thread half of loading: build annotation objects, then the displayed
    signal and analysis data (from the disk cache where still valid), drawing every
    panel."""
    events_to_ui(ui, events)
    ui.toolbar_jump_to_epoch.setMaximum(ui.numepo)

    def shown():
        apply_tf_visibility(ui)
        _update_export_menu_state(ui)
        if on_done is not None:
            on_done()

    settings_changed(ui, shown)
