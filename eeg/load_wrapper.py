from config.load_configuration import load_configuration
from scoring.load_scoring import load_scoring
from scoring.events_to_ui import events_to_ui
from utilities.timing_decorator import timing_decorator
from .load_eeglab import load_eeglab
from .load_r09 import load_r09
from .load_edf import load_edf
from .load_edf_volt import load_edf_volt
from .number_of_epochs import number_of_epochs
from cache.load_cache import load_cache
from signal_processing.times_vector import times_vector
from events.draw_event_in_this_epoch import draw_event_in_this_epoch
from utilities.apply_tf_visibility import apply_tf_visibility


@timing_decorator
def load_wrapper(ui, datatype):
    ui.this_epoch = 0
    if datatype == "eeglab":
        ui.eeg_data, srate, channel_names = load_eeglab(ui.filename)
    if datatype == "r09":
        ui.eeg_data, srate, channel_names = load_r09(ui.filename)    
    if datatype == "edf":
        ui.eeg_data, srate, channel_names = load_edf(ui.filename)    
    if datatype == "edfvolt":
        ui.eeg_data, srate, channel_names = load_edf_volt(ui.filename)    

    try:
        numchans = ui.eeg_data.shape[0]
    except:
        numchans = 6

    ui.config = load_configuration(f"{ui.filename}.config.json", numchans, srate, channel_names)
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
    ui.SignalWidget.draw_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)
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
    ui.TFWidget.draw_tf(ui.eeg_data, ui.times, ui.this_epoch, srate, ui.tf_freqs,
                        ui.tf_norm_median, ui.tf_norm_iqr, ui.tf_norm_rms, ui.tf_norm_median_linear,
                        display_mode, freq_scale, freq_limits,
                        time_unit, epoch_length, tf_channel_idx, tf_channel_label)
    apply_tf_visibility(ui)
    for container in ui.AnnotationContainer:
        draw_event_in_this_epoch(ui, container)
