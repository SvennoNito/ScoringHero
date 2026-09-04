import os
import numpy as np
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
from .align_channels import align_channels_to_config


def load_single(filename_prefix, datatype):
    """Load a single EEG file and return (eeg_data, srate, channel_names)."""
    if datatype == "eeglab":
        return load_eeglab(filename_prefix)
    if datatype == "r09":
        return load_r09(filename_prefix)
    if datatype == "edf":
        return load_edf(filename_prefix)
    if datatype == "edfvolt":
        return load_edf(filename_prefix, scale_to_uv=True)


@timing_decorator
def load_wrapper(ui, datatype, extra_files=None):
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

    ui.eeg_data, srate, channel_names = load_single(ui.filename, datatype)

    if extra_files:
        for filepath in extra_files:
            prefix, _ = os.path.splitext(filepath)
            extra_data, extra_srate, extra_channel_names = load_single(prefix, datatype)
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

    # Reset filter window so it is recreated with the new channel configuration
    ui.FilterWindow = None

    try:
        numchans = ui.eeg_data.shape[0]
    except:
        numchans = 6

    ui.config = load_configuration(f"{ui.filename}.config.json", numchans, srate, channel_names, ui.app_path)
    rebuild_channel_index(ui)

    # Reorder eeg_data rows to match the saved channel order in config, and
    # reconstruct derived channels (added via re-reference) that are not stored
    # in the EEG file, so the channel count/order matches config before
    # rebuild_eeg_data_display applies the re-reference.
    ui.eeg_data = align_channels_to_config(ui.eeg_data, channel_names, ui.config)

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

    events_to_ui(ui, events)

    times_vector(ui)
    ui.toolbar_jump_to_epoch.setMaximum(ui.numepo)
    ui.SignalWidget.draw_signal(ui.config, ui.eeg_data_display, ui.times, ui.this_epoch,
                                 get_overlay_signal_for_display(ui))
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)
    load_cache(ui)
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
