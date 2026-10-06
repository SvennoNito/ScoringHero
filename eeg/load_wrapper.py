import os
import numpy as np
from config.write_configuration import write_configuration
from config.load_configuration import load_configuration
from scoring.load_scoring import load_scoring
from scoring.events_to_ui import events_to_ui
from utilities.timing_decorator import timing_decorator
from utilities.channel_index import rebuild_channel_index
from .load_eeglab import load_eeglab
from .load_r09 import load_r09
from .load_edf import load_edf
from .number_of_epochs import number_of_epochs
from cache.load_cache import load_cache
from signal_processing.times_vector import times_vector
from events.draw_event_in_this_epoch import draw_event_in_this_epoch
from utilities.apply_tf_visibility import apply_tf_visibility
from utilities.refresh_gui import _update_export_menu_state
from utilities.overlay_state import get_active_analysis_data, get_overlay_signal_for_display
from .rebuild_display import rebuild_eeg_data_display
from utilities.busy_indicator import run_busy


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
    the loader now reports. Refresh the stored rate (other settings are kept) and
    drop the cached derived data so it is rebuilt."""
    if ui.config[0]["Sampling_rate_hz"] == srate:
        return
    ui.config[0]["Sampling_rate_hz"] = srate
    write_configuration(f"{ui.filename}.config.json", ui.config)
    cache_file = f"{ui.filename}.cache.pkl"
    if os.path.exists(cache_file):
        os.remove(cache_file)


def _reset_for_new_recording(ui):
    ui.this_epoch = 0

    # A newly loaded primary recording invalidates any loaded overlay signal
    # (different duration/channels), so drop it and reset the related menu state.
    ui.eeg_data_ref = None
    ui.eeg_data_display_ref = None
    ui.show_overlay = False
    ui.analysis_source = "original"
    if hasattr(ui, "action_remove_overlay"):
        ui.action_remove_overlay.setEnabled(False)
        ui.action_show_overlay.blockSignals(True)
        ui.action_show_overlay.setChecked(False)
        ui.action_show_overlay.blockSignals(False)
        ui.action_show_overlay.setEnabled(False)
        ui.menu_analyze_source.setEnabled(False)
        ui.action_analyze_original.blockSignals(True)
        ui.action_analyze_original.setChecked(True)
        ui.action_analyze_original.blockSignals(False)
        ui.action_analyze_overlay.blockSignals(True)
        ui.action_analyze_overlay.setChecked(False)
        ui.action_analyze_overlay.blockSignals(False)

    # Reset filter window so it is recreated with the new channel configuration
    ui.FilterWindow = None


@timing_decorator
def load_wrapper(ui, datatype, extra_files=None):
    """Synchronous load (used at startup, before the window is shown)."""
    _reset_for_new_recording(ui)
    events = _load_heavy(ui, datatype, extra_files)
    _show_loaded(ui, events)


def load_wrapper_busy(ui, datatype, extra_files, on_done, on_error):
    """Load with the heavy step off the GUI thread and a busy indicator on top."""
    _reset_for_new_recording(ui)

    def done(events):
        _show_loaded(ui, events)
        on_done()

    run_busy(ui, "Loading recording…",
             lambda: _load_heavy(ui, datatype, extra_files), done, on_error)


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

    ui.config = load_configuration(f"{ui.filename}.config.json", numchans, srate, channel_names, ui.app_path, units=units)
    _repair_stored_sampling_rate(ui, srate)
    rebuild_channel_index(ui)

    # One raw row per channel, in channel order: each channel (derived ones
    # included) shows the file signal at its Signal_index, so renamed and moved
    # channels keep their signal. rebuild_eeg_data_display applies the re-reference.
    ui.eeg_data = ui.eeg_data[[channel["Signal_index"] for channel in ui.config[1]]]

    # Keep the original-plus-derived data immutable; display copy is rebuilt below
    ui.eeg_data_display = ui.eeg_data.copy()

    # Apply all saved manipulations (re-reference + filter + flip) from config
    rebuild_eeg_data_display(ui)

    ui.numepo = number_of_epochs(
        ui.eeg_data.shape[1],
        ui.config[0]["Sampling_rate_hz"],
        ui.config[0]["Epoch_length_s"],
    )
    ui.stages, events = load_scoring(
        f"{ui.filename}.json", ui.config[0]["Epoch_length_s"], ui.numepo, "scoringhero"
    )

    times_vector(ui)
    load_cache(ui)
    return events


def _show_loaded(ui, events):
    """GUI-thread half of loading: build annotation objects and draw every panel."""
    events_to_ui(ui, events)
    ui.toolbar_jump_to_epoch.setMaximum(ui.numepo)
    ui.SignalWidget.draw_signal(ui.config, ui.eeg_data_display, ui.times, ui.this_epoch,
                                 get_overlay_signal_for_display(ui))
    ui.DisplayedEpochWidget.update_text(
        ui.this_epoch, ui.numepo, ui.stages, ui.stages_comparison, ui.comparison_name
    )
    ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)
    ui.HypnogramWidget.draw_hypnogram(ui)
    srate = ui.config[0]["Sampling_rate_hz"]
    display_mode = ui.config[0].get("Wavelet_display_mode", "Z-scored Power")
    freq_scale = ui.config[0].get("Wavelet_frequency_scale", "Logarithmic")
    freq_limits = ui.config[0].get("Wavelet_frequency_limits_hz", None)
    time_unit = ui.config[0].get("EEG_panel_time_unit", "Seconds")
    recording_start_time = ui.config[0].get("Recording_start_time", "00:00")
    epoch_length = ui.config[0]["Epoch_length_s"]
    tf_channel_label = ui.config[0].get("Wavelet_channel", "")
    tf_channel_idx = ui.channel_name_to_idx.get(tf_channel_label, 0)
    ui.TFWidget.draw_tf(get_active_analysis_data(ui), ui.times, ui.this_epoch, srate, ui.tf_freqs,
                        ui.tf_norm_median, ui.tf_norm_iqr, ui.tf_norm_rms, ui.tf_norm_median_linear,
                        display_mode, freq_scale, freq_limits,
                        time_unit, epoch_length, tf_channel_idx, tf_channel_label,
                        recording_start_time=recording_start_time)
    apply_tf_visibility(ui)
    for container in ui.AnnotationContainer:
        draw_event_in_this_epoch(ui, container)
    _update_export_menu_state(ui)
