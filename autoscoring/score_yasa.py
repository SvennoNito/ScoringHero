from mne import create_info
from mne.io import RawArray
from yasa import SleepStaging
from .autoscore_results import apply_yasa
from utilities.refresh_gui import refresh_gui


def score_yasa(ui):

    info = create_info(ch_names=[channel["Channel_name"] for channel in ui.config[1]], sfreq=125)
    raw  = RawArray(ui.eeg_data_display, info)

    # if raw.tmax/60 > 5:
    model = SleepStaging(raw, eeg_name=ui.config[1][0]["Channel_name"], eog_name="EOG1", emg_name="EMG")
    stages      = model.predict()
    probability = model.predict_proba()
    confidence  = probability.max(axis=1)

    apply_yasa(ui.scoring, stages, confidence)

    ui.save_scoring()
    ui.HypnogramWidget.draw_hypnogram(ui)
    refresh_gui(ui)
