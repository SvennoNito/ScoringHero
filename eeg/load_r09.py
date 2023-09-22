import numpy as np

def load_r09(filename_prefix):
    with open(f'{filename_prefix}.r09', 'rb') as file:
        data = np.fromfile(file, dtype=np.int16)

    # Reshape the data into separate channels
    num_channels    = 9
    data            = [data[i::num_channels] for i in range(num_channels-1, -1, -1)]
    srate           = 128
    return np.array(data), srate


# import matplotlib.pyplot as plt

# # Create a figure and axis for the plot
# fig, ax = plt.subplots()

# # Plot each vector separately
# ax.plot(channel_data[1])

# # Add labels, legend, and title
# ax.set_xlabel('Data Points')
# ax.set_ylabel('Values')
# ax.legend()
# ax.set_title('Plot of 9 Separate Vectors')

# # Show the plot
# plt.show()



# data_range = data.max() - data.min()
# bin_width = 1
# fig, ax = plt.subplots()
# num_bins = int(np.ceil(data_range / bin_width))

# # Create a histogram with bins of width 1
# plt.hist(data, bins=num_bins, edgecolor='k', align='left', rwidth=0.8)
# plt.show()