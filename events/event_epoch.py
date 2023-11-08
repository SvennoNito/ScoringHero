import numpy as np

def event_epoch(borders, epolen, max_number_epochs):
    epoch_from_to = [np.ceil(np.array(border) / epolen) for border in borders]
    epoch_array = [np.arange(start, end + 1).astype(int).tolist() for start, end in epoch_from_to]
    epoch_array = [[epoch for epoch in epochs if epoch <= max_number_epochs] for epochs in epoch_array]
    return epoch_array
