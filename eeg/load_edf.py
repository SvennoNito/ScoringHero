import numpy as np
import mne

def load_edf(filename_prefix):
    file            = f'{filename_prefix}.edf'
    data            = mne.io.read_raw_edf(file, preload=True)    
    eeg_data        = data.get_data()
    srate           = data.info['sfreq']
    channel_names   = data.info['ch_names']
    for ch in data.info['chs']:
        print(f"Channel: {ch['ch_name']}, Unit: {ch['unit']}")
    print(f"Min amplitude: {eeg_data[0].min()}, Max amplitude: {eeg_data[0].max()}")

    # MNE by default scales the data in volt I believe?
    #if data.info['chs'][0]['unit'] == 107:
    #    data.apply_function(lambda x: x * 1e6)
    #    eeg_data = data.get_data()
  
    return eeg_data, int(srate), channel_names
