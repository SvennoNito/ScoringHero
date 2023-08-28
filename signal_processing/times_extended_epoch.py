import numpy as np
from utilities import *


@timing_decorator
def times_extended_epoch(times_and_indices, this_epoch, epolen, extension_l, extension_r):
    times = times_and_indices[this_epoch][0]
    indices = times_and_indices[this_epoch][1]
    extend_by_numepo_r = np.ceil(extension_r / epolen).astype(int)
    extend_by_numepo_l = np.ceil(extension_l / epolen).astype(int)
    times_r = []
    indices_r = []
    [
        (times_r.extend(times), indices_r.extend(indices))
        for times, indices in times_and_indices[
            this_epoch + 1 : this_epoch + extend_by_numepo_r + 1
        ]
    ]
    times_l = []
    indices_l = []
    [
        (times_l.extend(times), indices_l.extend(indices))
        for times, indices in times_and_indices[this_epoch - extend_by_numepo_l : this_epoch]
    ]

    extend_by_r = find_closest_index(times_r, times[-1] + extension_r)
    extend_by_l = find_closest_index(times_l, times[0] - extension_l)

    extended_times = np.concatenate((times_l[extend_by_l:], times, times_r[:extend_by_r]))
    extended_indices = np.concatenate(
        (indices_l[extend_by_l:], indices, indices_r[:extend_by_r])
    ).astype(int)
    return extended_times, extended_indices


def find_closest_index(number_list, target):
    if len(number_list) > 0:
        closest_index = min(range(len(number_list)), key=lambda i: abs(number_list[i] - target))
    else:
        closest_index = None
    return closest_index
