import os, json
from .load_scoringhero import load_scoringhero
from .load_vis import load_vis
from .load_yasa import load_yasa
from .load_sleeptrip import load_sleeptrip
from .load_sleepyland import load_sleepyland

def load_scoring(scoring_filename, epolen, numepo, filetype):

    if filetype == "scoringhero":
        scoring_data, annotations = load_scoringhero(scoring_filename, epolen, numepo)

    if filetype == "vis":
        scoring_data, annotations = load_vis(scoring_filename, epolen, numepo)

    if filetype == "yasa":
        scoring_data, annotations = load_yasa(scoring_filename, epolen, numepo)        

    if filetype == "sleeptrip":
        scoring_data, annotations = load_sleeptrip(scoring_filename, epolen, numepo)        

    if filetype == "sleepyland":
        scoring_data, annotations = load_sleepyland(scoring_filename, epolen, numepo)        

    return scoring_data, annotations
