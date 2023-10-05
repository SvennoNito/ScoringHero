import os, json, sys
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QApplication, QMessageBox,QPushButton
from .default_scoring import default_scoring

def load_vis(scoring_filename, epolen, numepo, track=1):

    if epolen != 20:
        msg = QMessageBox.warning(None, 'Warning',
                                  f'Zurich scoring is usually in 20s. Your epoch length is set to {epolen}s. Is that intentional?',
                                  QMessageBox.Cancel | QMessageBox.Ok)
        if msg == QMessageBox.Ok:
            pass
        else:
            return       

    if os.path.exists(scoring_filename):
        visdata = []

        # Open the VIS file to read the data
        with open(scoring_filename, 'r') as file:
            # Skip the first line as it contains metadata (offset value in MATLAB code)
            offset_line = file.readline()
            offs = int(offset_line.strip())

            # Read the rest of the file
            for line in file:
                # Split the line into columns assuming space as delimiter
                columns = line.strip().split()
                if len(columns) >= 2 and len(columns) <= 3:  # Ensure there are at least three columns
                    epoch, sleep_stage = columns[:2]
                    visdata.append([int(epoch), sleep_stage])

        # Convert to a NumPy array for consistency with MATLAB's matrix format
        visdata = np.array(visdata, dtype=object)
        visdata[-1][1] = visdata[-2][1]

        df = pd.DataFrame(visdata, columns=['Epoch', 'SleepStage'])
        df.set_index('Epoch', inplace=True)
        df = df.reindex(range(1, visdata[-1][0] + 1))  # Assuming you want to include the last epoch as well
        df.fillna(method='bfill', inplace=True)
        df.fillna(method='ffill', inplace=True)
        df = df['SleepStage'].values
        annotations = []

        mapping = {'0': 'Wake', '1': 'N1', '2': 'N2', '3': 'N3', 'r': 'REM', 'e': 'Wake'}
        vissymb = np.vectorize(mapping.get)(df)
        mapping_numeric = {'Wake': 1, 'N1': -1, 'N2': -2, 'N3': -3, 'REM': 0, }
        visnum = np.vectorize(mapping_numeric.get)(vissymb)        

        scoring_data = []
        for counter, (str, num) in enumerate(zip(vissymb, visnum)):
            template = {
                "epoch": counter + 1,
                "start": counter * epolen,
                "end": (counter + 1) * epolen,
                "stage": str,
                "digit": int(num),
                "uncertain": 0,
                "channels": [],
                "clean": 1,
            }
            scoring_data.append(template)        

    return scoring_data, annotations