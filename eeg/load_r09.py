import numpy as np

def load_r09(filename_prefix):
    with open(f'{filename_prefix}.r09', 'rb') as file:
        data = np.fromfile(file, dtype=np.int16)

    # Reshape the data into separate channels
    num_channels    = 9
    data            = [data[i::num_channels] for i in [3,4,5,6,7,8,1,2,0]]
    srate           = 128
    channel_names   = ["F3-A2", "F4-A1", "C3-A2", "C4-A1", "O1-A2", "O2-A1", "EOG1", "EOG2", "EMG"]
    return np.array(data), srate, channel_names
