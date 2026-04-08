import os
from .default_scoring import default_scoring
import numpy as np
import csv

def load_gssc(scoring_filename, epolen, numepo):
    mapping_str = {
        0: 'Wake',
        1: 'N1',
        2: 'N2',
        3: 'N3',
        4: 'REM',
    }
    mapping_num = {
        'Wake': 1,
        'N1': -1,
        'N2': -2,
        'N3': -3,
        'REM': 0
    }

    scoring_str = []
    scoring_num = []
    confidence_list = []

    if os.path.exists(scoring_filename):
        with open(scoring_filename, "r") as file:
                
            # Skip header
            next(file)
            for line in file:
                if not line.strip():
                    continue
                
                parts = line.strip().split(',')
                if parts[0] == 'Epoch':
                    continue  # Skip header line

                stage_key   = int(parts[2])
                stage_str   = mapping_str.get(stage_key)
                stage_num   = mapping_num.get(stage_str)
                conf        = float(parts[3 + stage_key])

                scoring_str.append(stage_str)
                scoring_num.append(stage_num)
                confidence_list.append(conf)

        # Initialize scoring_data
        scoring_data = default_scoring(epolen, numepo)
        for counter, (str_val, num_val, conf_val) in enumerate(zip(scoring_str, scoring_num, confidence_list)):
            if counter < len(scoring_data):
                scoring_data[counter]["digit"] = int(num_val)
                scoring_data[counter]["stage"] = str_val
                scoring_data[counter]["source"] = "GSSC"
                scoring_data[counter]["confidence"] = conf_val

        # If GSSC did not score the last epoch(s), copy the second-to-last scored epoch
        n_scored = len(scoring_str)
        if 0 < n_scored < numepo:
            last = scoring_data[n_scored - 1]
            for i in range(n_scored, numepo):
                scoring_data[i]["digit"] = last["digit"]
                scoring_data[i]["stage"] = last["stage"]
                scoring_data[i]["source"] = last["source"]
                scoring_data[i]["confidence"] = last["confidence"]

    else:
        print("Could not find scoring file")
        return None, []

    # If scoring_str and scoring_num are needed for compatibility with old code, they are already populated
    return scoring_data, []
