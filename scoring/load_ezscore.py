import os

from .default_scoring import default_scoring

# ezscore-f hypnogram codes, as written by ezscore_demo.py
mapping_str = {
    1: "N1",
    2: "N2",
    3: "N3",
    4: "REM",
    5: "Wake",
    6: None,      # artifact — deliberately left unscored
}

mapping_num = {
    "N1":   -1,
    "N2":   -2,
    "N3":   -3,
    "REM":   0,
    "Wake":  1,
}


def load_ezscore(scoring_filename, epolen, numepo):
    """Read an ezscore-f hypnogram CSV (one integer code per 30 s epoch).

    Epochs classified as artifact (code 6) stay unscored and are flagged as
    unclean, so they are excluded from the sleep statistics.
    """
    if not os.path.exists(scoring_filename):
        print("Could not find scoring file")
        return None, []

    codes = []
    with open(scoring_filename, "r") as file:
        for line in file:
            field = line.strip().split(",")[0].strip().strip('"')
            if not field:
                continue
            try:
                codes.append(int(float(field)))
            except ValueError:
                continue  # header or comment line

    scoring_data = default_scoring(epolen, numepo)

    for counter, code in enumerate(codes):
        if counter >= len(scoring_data):
            break
        stage_str = mapping_str.get(code)
        scoring_data[counter]["source"] = "ezscore-f"
        if stage_str is None:
            scoring_data[counter]["clean"] = 0 if code == 6 else 1
            continue
        scoring_data[counter]["stage"] = stage_str
        scoring_data[counter]["digit"] = mapping_num[stage_str]

    return scoring_data, []
