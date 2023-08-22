import numpy as np

def signal_times_vector(npoints, srate, epolen, extend_l, extend_r):
    times_vector                        = np.arange(0, npoints) / srate
    times_vector_epoched = turn_into_epochs(times_vector, epolen, srate, extend_l, extend_r)
    return times_vector_epoched, len(times_vector_epoched)


def turn_into_epochs(times_vector, epolen, srate, extend_l, extend_r):
    num_epochs              = int(np.ceil(times_vector[-1] / epolen))
    epoched_times_vector    = []
    start_indices           = np.arange(0, num_epochs) * epolen * srate
    end_indices             = np.minimum(start_indices + epolen * srate, len(times_vector))

    # Add extensions
    start_indices_ext = start_indices - extend_l*srate
    end_indices_ext   = end_indices + extend_r*srate

    # Remove impossible numbers
    start_indices_ext[start_indices_ext < 0] = 0
    end_indices_ext[end_indices_ext > epolen*srate*num_epochs] = epolen*srate*num_epochs

    for start_ext, end_ext, start, end in zip(start_indices_ext, end_indices_ext, start_indices, end_indices):
        epoch_times     = times_vector[start_ext:end_ext]
        epoch_indices   = np.array(range(start_ext, end_ext))
        epoch_border    = (start/srate, end/srate)
        #epoch_indices[epoch_indices < 0] = 0
        #epoch_indices[epoch_indices > 0] = 0
        epoched_times_vector.append((epoch_times, epoch_indices, epoch_border))
    
    return epoched_times_vector