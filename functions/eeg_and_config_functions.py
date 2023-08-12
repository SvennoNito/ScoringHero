import os, json, scipy, h5py



# *** EEG file functions *** 
# **************************

def load_eeg_and_configuration_settings(eeg_filename, EEG):
    eeg_filename_without_extension, extension = os.path.splitext(eeg_filename)

    # Load EEG data
    if extension == '.mat':
        if scipy.io.matlab.miobase.get_matfile_version(eeg_filename_without_extension)[0] == 2: #v7.3 files
            with h5py.File(eeg_filename_without_extension, "r") as eeg_file:
                eeg_data = eeg_file['EEG']['eeg_data'][:]
                if eeg_data.shape[0] > eeg_data.shape[1]: # dimensions are weird ....
                    eeg_data = eeg_data.T
        else:
            eeg_data = scipy.io.loadmat(eeg_filename_without_extension)['EEG']['data'][0][0]
    number_of_channels = eeg_data.shape[0]

    # Integrate EEG data into structure
    EEG.data = eeg_data

    # Load and apply configuration settings
    configuration_settings = load_configuration_file(eeg_filename_without_extension + '.config.json', number_of_channels)
    apply_configuration_settings(EEG, configuration_settings)

    return eeg_filename_without_extension


# *** Configuration file functions *** 
# ************************************

def apply_configuration_settings(EEG, configuration_settings):
    EEG.add_info(configuration_settings[0])
    EEG.add_chaninfo(configuration_settings[1])  
    EEG.update()


def load_configuration_file(configuration_filename, number_of_channels=6):
    if os.path.exists(configuration_filename):
        with open(configuration_filename, "r") as file:
            configuration_settings = json.load(file)

    else:
        configuration_settings = build_default_configuration(number_of_channels)
        write_configuration_file(configuration_filename, configuration_settings)
        
    return configuration_settings


def write_configuration_file(configuration_filename, configuration_settings):
        with open(configuration_filename, "w") as file:
            json.dump(configuration_settings, file, indent=4)   


def build_default_configuration(number_of_channels, srate = 125):
    configuration_settings      = [[] for x in range(2)]
    configuration_settings[0]   = { 
                    "Sampling_rate_hz": srate,
                    "Epoch_length_s": 30, 
                    "Channel_index_for_spectogram": 1,
                    "Extension_epoch_left_s": 5,
                    "Extension_epoch_right_s": 5
                    }
    
    configuration_settings[1] = [{
        "Channel_name": f'Channel {chan+1}',
        "Channel_color": "Black",
        "Display_on_screen": 1 if chan < 9 else 0,
        "Scaling_factor": 1
    }
    for chan in range(number_of_channels)]

    return configuration_settings       


def update_channel_information_in_configuration_file(configuration_filename, channel_information):
    configuration_settings      = load_configuration_file(configuration_filename)
    configuration_settings[1]   = channel_information
    with open(configuration_filename, 'w') as file:
        json.dump(configuration_settings, file, indent=4)    









"""     else: # Create default configuration configuration_settings
        root = tk.Tk() 
        root.withdraw() 
        display_text    = "Configuration file «EEG_filename».json was not found. Loading default configuration_settings instead. \nIf you want to have more meaningful channel labels than «channel 1» or want to avoid this pop-up box, create a .json file named as your EEG file in the same folder as your EEG file. \nYou can use the function «build_json.py» for that or copy an existing .json file and adapt the values accordingly. \nTo continue for now, define the sampling rate of your data here (in Hz):"
        srate           = tk.simpledialog.askstring("Configuration file not found", display_text, parent=root)
        srate           = int(re.findall(r'\d+', srate)[0])
        # ctypes.windll.user32.MessageBoxW(0, "Configuration file «EEG_filename».json was not found. Loading default configuration_settings with a sampling rate of 125 Hz instead. If your data has a different sampling rate or you want to have more meaningful channel labels than «channel 1», create a .json file named as your EEG file in the same folder as your EEG file. You can use the function  «build_json.py» for that or copy an existing .json file and adapt the values accordingly.", "No configuration file found", 1)
        configuration_settings = default_config(srate, EEG.data.shape[0]) """
  