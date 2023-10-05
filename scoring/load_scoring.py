import os, json
from .load_scoringhero import load_scoringhero
from .load_vis import load_vis

def load_scoring(scoring_filename, epolen, numepo, filetype):

    if filetype == "scoringhero":
        scoring_data, annotations = load_scoringhero(scoring_filename, epolen, numepo)

    if filetype == "vis":
        scoring_data, annotations = load_vis(scoring_filename, epolen, numepo)

    return scoring_data, annotations
