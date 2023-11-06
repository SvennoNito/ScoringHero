from signal_processing.sample_from_selection import sample_from_selection
from signal_processing.channel_from_selection import channel_from_selection

def eeg_from_rectangle(ui, converted_corners, converted_shape):

    # Selected sample points
    samples, times = sample_from_selection(ui.times, ui.this_epoch, converted_corners[-1])

    # Select channel
    displayed_channel, channel = channel_from_selection(ui.config, converted_corners[-1], converted_shape[-1])
    print(f'Drawn rectangle selected EEG data of {ui.config[1][channel]["Channel_name"]} (visible channel no. {displayed_channel+1}) in the time between {times[0]} and {times[-1]}s')

    # Compute power
    data = ui.eeg_data[channel][samples]      

    return data, times