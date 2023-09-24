from config.load_configuration import load_configuration
from scoring.load_scoring import load_scoring
from scoring.events_to_ui import events_to_ui
from utilities.timing_decorator import timing_decorator
from .load_eeglab import load_eeglab
from .load_r09 import load_r09
from .number_of_epochs import number_of_epochs


@timing_decorator
def load_wrapper(ui, datatype):
    if datatype == "eeglab":
        ui.eeg_data, srate, channel_names = load_eeglab(ui.filename)
    if datatype == "r09":
        ui.eeg_data, srate, channel_names = load_r09(ui.filename)        

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
        f"{ui.filename}.json", ui.config[0]["Epoch_length_s"], ui.numepo
    )

    # if datatype == "r09":
    #     channel_names = ["F3-A2", "F4-A1", "C3-A2", "C4-A1", "O1-A2", "O2-A1", "EOG1", "EOG2", "EMG"]
    #     for (channel, name) in zip(ui.config[1], channel_names):
    #         channel["Channel_name"]     = name

    events_to_ui(ui, events)
