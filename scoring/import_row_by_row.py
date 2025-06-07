import re, warnings

def import_row_by_row(string_to_check, lines, mapping_str, mapping_num, numepo):
    """
    This function is a placeholder for importing rows.
    It currently does nothing but can be expanded in the future.
    """

    scoring_str = []
    scoring_num = []    
    equality_check = False

    for row, item in enumerate(lines):
        item            = item.strip()
        found_chars     = re.match(string_to_check, item, re.IGNORECASE)

        if not found_chars:  # skip rows
            print(f"Row {row} in scoringfile reads '{item}. None of the specified strings '{string_to_check}' was found. Skipping this row.")
            continue                

        if len(scoring_str) - numepo == 0 and equality_check:
            total_lines = len(lines) 
            raise ValueError(
                f"Error! Imported sleep scoring file has MANY more epochs ({total_lines}) than expected ({numepo}). Was the scoring performed with the same epoch length as currently displayed in scoringhero?",
            )   

        if len(scoring_str) - numepo == 0:
            warnings.warn(
                f"Warning! Imported sleep scoring file has 1 more epoch than expected. Scoringhero discards epochs with only partial data present. Hence, last scored epoch will be ignored.",        
                UserWarning
            )
            equality_check = True
            continue	              
        
        scoring_str.append(mapping_str[found_chars[0]])
        scoring_num.append(mapping_num[scoring_str[-1]])        

    return scoring_str, scoring_num