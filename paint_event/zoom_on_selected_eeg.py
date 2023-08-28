import matplotlib.pyplot as plt
from .selected_samples import selected_samples
from .selected_channel import selected_channel

def zoom_on_selected_eeg(ui):

    data, times = ui.PaintEventWidget.selected_data
    times -= times[0]
    
    figure, ax = plt.subplots()
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Amplitude \u03BCV')        
    ax.plot(times, data)
    plt.show()