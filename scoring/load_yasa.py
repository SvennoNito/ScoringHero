import os, json, re, warnings
from .default_scoring import default_scoring
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
            for row, item in enumerate(lines):
                string_to_check = r'N[123]|NREM[123]|WAKE|REM|W|R|[01234]'	
                found_chars     = re.findall(string_to_check, item)

                if not found_chars:  # skip rows
                    print(f"Row {row} in {scoring_filename} reads '{item.strip()}. None of the specified strings '{string_to_check}' was found. Skipping this row.")
                    continue

                if row >= numepo:  # sanity check
                    total_lines = len(lines)
                    additional_lines_threshold = 100
                    if total_lines >= numepo + additional_lines_threshold:
                        raise ValueError(
                        f"Error! Imported sleep scoring file has MUCH more epochs ({total_lines}) than expected ({numepo}). When the file has {additional_lines_threshold} lines more than expected, it is assumed that something is off. Was the scoring performed with the same epoch length as currently displayed in scoringhero?",
                        )
                    else:
                        warnings.warn(
                            f"Warning! Imported sleep scoring file has more epochs ({total_lines}) than expected ({numepo}). Only the first {numepo} scored epochs will be used.",        
                            UserWarning
                        )
                    break        

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

        