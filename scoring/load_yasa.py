import os, json, re, warnings
from .default_scoring import default_scoring
from .import_row_by_row import import_row_by_row
import numpy as np

def load_yasa(scoring_filename, epolen, numepo):

    mapping_str = {'W': 'Wake', 
                   'Wake': 'Wake', 
                   'WAKE': 'Wake', 
                   '0': 'Wake',                   
                   'N1': 'N1', 
                   'NREM1': 'N1',
                   '1': 'N1',
                   'N2': 'N2', 
                   'NREM2': 'N2', 
                   '2': 'N2',
                   'N3': 'N3', 
                   '3': 'N3',
                   'NREM3': 'N3', 
                   'R': 'REM',
                   'Rem': 'REM',
                   'REM': 'REM',
                   '4': 'REM'}
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
 
            [scoring_str, scoring_num] = import_row_by_row(r'^\s*(N[123]|NREM[123]|WAKE|REM|W|R|[01234])\s*$', lines, mapping_str, mapping_num, numepo)        

            scoring_data = default_scoring(epolen, numepo)

            for counter, (str, num) in enumerate(zip(scoring_str, scoring_num)):
                scoring_data[counter]["digit"]  = int(num)
                scoring_data[counter]["stage"]  = str
                # scoring_data[counter]["source"] = "YASA"

    else:
        print("Could not find scoring file")

    return scoring_data, []

        