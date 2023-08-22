import os, json
from .default_scoring import default_scoring

def load_scoring(scoring_filename, numepo, epolen):
    if os.path.exists(scoring_filename):
        with open(scoring_filename, "r") as file:
            json_data    = json.load(file)
            annotations  = json_data[1]
            scoring_data = json_data[0]
    else:
        annotations  = []
        scoring_data = default_scoring(numepo, epolen)    
    return scoring_data, annotations