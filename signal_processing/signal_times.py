import numpy as np
from my_utilities import *

def signal_times_vector(ui):

    npoints         = ui.eeg_data.shape[1]
    srate           = ui.config[0]['Sampling_rate_hz']
    epolen          = ui.config[0]['Epoch_length_s']
    extend_l        = ui.config[0]['Extension_epoch_left_s']
    extend_r        = ui.config[0]['Extension_epoch_right_s']    

    times_vector    = np.arange(0, npoints) / srate
    ui.times        = turn_into_epochs(times_vector, epolen, srate, extend_l, extend_r)


def turn_into_epochs(times_vector, epolen, srate, extend_l, extend_r):
    num_epochs              = int(np.floor(times_vector[-1] / epolen))
    epoched_times_vector    = []
    start_indices           = np.arange(0, num_epochs) * epolen * srate
    end_indices             = np.minimum(start_indices + epolen * srate, len(times_vector))

    # Add extensions
    start_indices_ext = start_indices - extend_l*srate
    end_indices_ext   = end_indices + extend_r*srate

    # Remove impossible numbers
    start_indices_ext[start_indices_ext < 0] = 0
    end_indices_ext[end_indices_ext > int(np.floor(times_vector[-1]*srate))] = int(np.floor(times_vector[-1]*srate))

    for start_ext, end_ext, start, end in zip(start_indices_ext, end_indices_ext, start_indices, end_indices):
        epoch_times     = times_vector[start_ext:end_ext]
        epoch_indices   = np.array(range(start_ext, end_ext))
        epoch_border    = (start/srate, end/srate)
        #epoch_indices[epoch_indices < 0] = 0
        #epoch_indices[epoch_indices > 0] = 0
        epoched_times_vector.append((epoch_times, epoch_indices, epoch_border))
    
    return epoched_times_vector