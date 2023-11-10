from mne import create_info
from mne.io import RawArray
from yasa import SleepStaging
import numpy as np
from .write_scoring import write_scoring


def score_yasa(ui):

    info = create_info(ch_names=[channel["Channel_name"] for channel in ui.config[1]], sfreq=125)
    raw  = RawArray(ui.eeg_data, info)

    # if raw.tmax/60 > 5:
    model = SleepStaging(raw, eeg_name=ui.config[1][0]["Channel_name"], eog_name="EOG1", emg_name="EMG")
    stages      = model.predict()
    probability = model.predict_proba()
    confidence  = probability.max(axis=1)

    # Rename stages
    mapping = {'W': 'Wake', 'R': 'REM', 'N1': 'N1', 'N2': 'N2', 'N3': 'N3'}
    stages  = np.vectorize(mapping.get)(stages)    
    mapping = {'Wake': 1, 'REM': 0, 'N1': -1, 'N2': -2, 'N3': -3}
    digits  = np.vectorize(mapping.get)(stages)  

    for iepoch, epoch in enumerate(ui.stages):
        epoch["stage"]  = stages[iepoch]
        epoch["digit"]  = int(digits[iepoch])
        epoch["source"] = "YASA"
        epoch["confidence"] = np.round(confidence[iepoch], 4)

    # Update display text
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)

    # Update hypnpgram
    ui.HypnogramWidget.draw_hypnogram(ui)
    write_scoring(ui)        
