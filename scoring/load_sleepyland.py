import os
from .default_scoring import default_scoring
import numpy as np

def load_sleepyland(scoring_filename, epolen, numepo):
    mapping_str = {
        'W': 'Wake',
        'N1': 'N1',
        'N2': 'N2',
        'N3': 'N3',
        'R': 'REM',
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
                parts = line.strip().split('\t')
                if len(parts) < 6:
                    continue  # skip malformed lines

                # Extract stage, start, stop, and meta
                stage_key   = parts[1].strip()
                stage       = mapping_str.get(stage_key)
                meta        = parts[5].strip()

                # Parse meta for confidence values
                conf = {}
                for item in meta.split(';'):
                    if '=' in item:
                        k, v = item.split('=')
                        conf[k.strip()] = float(v.strip())

                # Assign confidence for the current stage
                if stage == 'Wake':
                    confidence = conf.get('pW')
                elif stage == 'N1':
                    confidence = conf.get('pN1')
                elif stage == 'N2':
                    confidence = conf.get('pN2')
                elif stage == 'N3':
                    confidence = conf.get('pN3')
                elif stage == 'REM':
                    confidence = conf.get('pR')
                else:
                    confidence = None

                scoring_str.append(stage)
                scoring_num.append(mapping_num[stage])
                confidence_list.append(confidence)

        # Initialize scoring_data
        scoring_data = default_scoring(epolen, numepo)
        for counter, (str_val, num_val, conf_val) in enumerate(zip(scoring_str, scoring_num, confidence_list)):
            if counter < len(scoring_data):
                scoring_data[counter]["digit"] = int(num_val)
                scoring_data[counter]["stage"] = str_val
                scoring_data[counter]["source"] = "Sleepyland"
                scoring_data[counter]["confidence"] = conf_val

    else:
        print("Could not find scoring file")
        return None, []

    # If scoring_str and scoring_num are needed for compatibility with old code, they are already populated
    return scoring_data, []
