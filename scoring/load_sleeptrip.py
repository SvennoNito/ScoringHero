import os, json, re, csv, warnings
from .default_scoring import default_scoring
from .import_row_by_row import import_row_by_row
import numpy as np

def load_sleeptrip(scoring_filename, epolen, numepo):

    mapping_str = {'0': 'Wake', 
                   '1': 'N1', 
                   '2': 'N2', 
                   '3': 'N3', 
                   '5': 'REM'}
    mapping_num = {'Wake': 1, 
                   'N1': -1, 
                   'N2': -2, 
                   'N3': -3, 
                   'REM': 0}    

    if os.path.exists(scoring_filename):
        with open(scoring_filename, "r", newline='') as csvfile:
            all_lines = list(csv.reader(csvfile))

            # Extract first column for scoring
            first_col = [row[0] for row in all_lines if row]

            # Extract second column (per-epoch event) if present
            epoch_event_col = []
            if all_lines and any(len(row) >= 2 for row in all_lines):
                for row in all_lines:
                    if len(row) >= 2:
                        try:
                            epoch_event_col.append(int(row[1]))
                        except (ValueError, IndexError):
                            epoch_event_col.append(0)
                    else:
                        epoch_event_col.append(0)

            [scoring_str, scoring_num] = import_row_by_row(r'^[01235]$', first_col, mapping_str, mapping_num, numepo)

            scoring_data = default_scoring(epolen, numepo)

            for counter, (str, num) in enumerate(zip(scoring_str, scoring_num)):
                scoring_data[counter]["digit"]  = int(num)
                scoring_data[counter]["stage"]  = str
                scoring_data[counter]["source"] = "Sleeptrip"

    else:
        print("Could not find scoring file")

    return scoring_data, epoch_event_col

        