import os
import numpy as np
from config.load_configuration import load_configuration
from scoring.load_scoring import load_scoring
from scoring.events_to_ui import events_to_ui
from utilities.timing_decorator import timing_decorator
from .load_eeglab import load_eeglab
from .load_r09 import load_r09
from .load_edf import load_edf
from .number_of_epochs import number_of_epochs
from cache.load_cache import load_cache
from signal_processing.times_vector import times_vector
from events.draw_event_in_this_epoch import draw_event_in_this_epoch
from utilities.apply_tf_visibility import apply_tf_visibility
from .rebuild_display import rebuild_eeg_data_display


def _load_single(filename_prefix, datatype):
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
    ui.eeg_data, srate, channel_names = _load_single(ui.filename, datatype)

    if extra_files:
        for filepath in extra_files:
            prefix, _ = os.path.splitext(filepath)
            extra_data, extra_srate, extra_channel_names = _load_single(prefix, datatype)
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

    ui.config = load_configuration(f"{ui.filename}.config.json", numchans, srate, channel_names)

    # Reorder eeg_data rows to match the saved channel order in config.
    # When the user reorders channels in the config window, config[1] is saved in
    # the new order but the EEG file always loads channels in the original file order.
    # We must permute eeg_data so that eeg_data[i] corresponds to config[1][i].
    non_derived_configs = [ch for ch in ui.config[1] if not ch.get("derived", False)]
    name_to_file_idx = {name: i for i, name in enumerate(channel_names)}
    config_names = [ch["Channel_name"] for ch in non_derived_configs]
    if (len(config_names) == len(channel_names)
            and all(n in name_to_file_idx for n in config_names)):
        new_order = [name_to_file_idx[n] for n in config_names]
        ui.eeg_data = ui.eeg_data[new_order]

    # Reconstruct derived channels (added via re-reference) that are not stored in the
    # EEG file. For each derived channel, find its source channel among the non-derived
    # entries and append a copy of that raw signal row to eeg_data so that the channel
    # count matches config before rebuild_eeg_data_display applies the re-reference.
    for ch_config in ui.config[1]:
        if ch_config.get("derived", False):
            src_name = ch_config.get("source_channel", ch_config["Channel_name"])
            src_idx = next(
                (i for i, c in enumerate(ui.config[1])
                 if c["Channel_name"] == src_name and not c.get("derived", False)),
                None,
            )
            if src_idx is not None and src_idx < ui.eeg_data.shape[0]:
                ui.eeg_data = np.vstack([ui.eeg_data, ui.eeg_data[src_idx:src_idx + 1]])
            else:
                ui.eeg_data = np.vstack([ui.eeg_data, np.zeros((1, ui.eeg_data.shape[1]))])

    # Keep the original-plus-derived data immutable; display copy is rebuilt below
    ui.eeg_data_display = ui.eeg_data.copy()

    # Apply all saved manipulations (filter + re-reference + flip) from config
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
    ui.SignalWidget.draw_signal(ui.config, ui.eeg_data_display, ui.times, ui.this_epoch)
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)
    load_cache(ui)
    ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)
    ui.HypnogramWidget.draw_hypnogram(ui)
    srate = ui.config[0]["Sampling_rate_hz"]
    display_mode = ui.config[0].get("Wavelet_display_mode", "Z-scored Power")
    freq_scale = ui.config[0].get("Wavelet_frequency_scale", "Logarithmic")
    freq_limits = ui.config[0].get("Wavelet_frequency_limits_hz", None)
    time_unit = ui.config[0].get("EEG_panel_time_unit", "Seconds")
    epoch_length = ui.config[0]["Epoch_length_s"]
    tf_channel_label = ui.config[0].get("Wavelet_channel", "")
    channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
    tf_channel_idx = channel_labels.index(tf_channel_label) if tf_channel_label in channel_labels else 0
    ui.TFWidget.draw_tf(ui.eeg_data_display, ui.times, ui.this_epoch, srate, ui.tf_freqs,
                        ui.tf_norm_median, ui.tf_norm_iqr, ui.tf_norm_rms, ui.tf_norm_median_linear,
                        display_mode, freq_scale, freq_limits,
                        time_unit, epoch_length, tf_channel_idx, tf_channel_label)
    apply_tf_visibility(ui)
    for container in ui.AnnotationContainer:
        draw_event_in_this_epoch(ui, container)
