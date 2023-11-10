import numpy as np

def event_epoch(borders, epolen, max_number_epochs):
    epoch_from_to = [np.ceil(np.array(border) / epolen) for border in borders]
    epoch_array = [np.arange(start, end + 1).astype(int).tolist() for start, end in epoch_from_to]
    epoch_array = [[epoch for epoch in epochs if epoch <= max_number_epochs] for epochs in epoch_array]

    # Whole epochs should only refer to the actual epoch
    full_epochs = np.where([border[1] - border[0] == epolen for border in borders])[0] 
    for epoch in full_epochs:
        epoch_array[epoch] = [epoch_array[epoch][1]]

    return epoch_array
