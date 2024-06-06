import os, json, re
from .default_scoring import default_scoring
import numpy as np

def load_yasa(scoring_filename, epolen, numepo):

    mapping_str = {'W': 'Wake', 
                   'Wake': 'Wake', 
                   'WAKE': 'Wake', 
                   'N1': 'N1', 
                   'NREM1': 'N1',
                   'N2': 'N2', 
                   'NREM2': 'N2', 
                   'N3': 'N3', 
                   'NREM3': 'N3', 
                   'R': 'REM',
                   'Rem': 'REM',
                   'REM': 'REM'}
    mapping_num = {'Wake': 1, 
                   'N1': -1, 
                   'N2': -2, 
                   'N3': -3, 
                   'REM': 0}    
    scoring_str = []
    scoring_num = []

    if os.path.exists(scoring_filename):
        with open(scoring_filename, "r") as file:
            lines = file.readlines()
            for item in lines:
                found_chars  = re.findall(r'N[123]|NREM[123]|[WR]|[WAKE]|[REM]', item)
                scoring_str.append(mapping_str[found_chars[0]])
                scoring_num.append(mapping_num[scoring_str[-1]])

            scoring_data = default_scoring(epolen, numepo)


            for counter, (str, num) in enumerate(zip(scoring_str, scoring_num)):
                scoring_data[counter]["digit"]  = int(num)
                scoring_data[counter]["stage"]  = str
                # scoring_data[counter]["source"] = "YASA"

    else:
        print("Could not find scoring file")

    return scoring_data, []

        