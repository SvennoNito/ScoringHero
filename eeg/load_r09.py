import numpy as np

def load_r09(filename_prefix):
    with open(f'{filename_prefix}.r09', 'rb') as file:
        data = np.fromfile(file, dtype=np.int16)

    # Reshape the data into separate channels
    num_channels    = 9
    data            = [data[i::num_channels] for i in [3,4,5,6,7,8,1,2,0]]
    srate           = 128
    return np.array(data), srate
