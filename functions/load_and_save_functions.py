import os, json, scipy, h5py, random



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


def choose_random_file_from_selection(files):
    rand_index  = random.randint(0, len(files) - 1)
    file        = files[rand_index]
    return file


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


def update_general_information_in_configuration_file(configuration_filename, channel_information):
    configuration_settings      = load_configuration_file(configuration_filename)
    configuration_settings[0]   = channel_information
    with open(configuration_filename, 'w') as file:
        json.dump(configuration_settings, file, indent=4)  


# *** Load and save scoring file ***
# **********************************

def load_scoring_file(scoring_filename, hypnogram, containers, spectogram_axes, EEG):
    if os.path.exists(scoring_filename):
        with open(scoring_filename, "r") as file:
            scoring_data = json.load(file)     
            integrate_loaded_scoring_file(scoring_data, hypnogram, containers, spectogram_axes, EEG)
            
        
def integrate_loaded_scoring_file(scoring_data, hypnogram, containers, spectogram_axes, EEG):
    # Load sleep stages
    # for bucket in scoring_data[0]:
        #hypnogram.assign(bucket['epoch'], bucket['stage'], bucket['channels'], bucket['uncertainty'])
    hypnogram.initiate(EEG)
    hypnogram.integrate_saved_epoch(scoring_data[0])
    
    # Load annotations
    for container, label in zip(containers, scoring_data[1][0].keys()):
        container.label     = label
        container.borders   = scoring_data[1][0][label]    
    #hypnogram.add_to_spectogram(1, spectogram_axes, containers)


def write_scoring_file(scoring_filename, epolen, hypnogram, artefacts, containers):
    with open(scoring_filename, mode='w', newline='') as file:
        if not scoring_filename.endswith(".json"):
            scoring_filename = f'{scoring_filename}.json'

        # Sleep stages
        saver = [[]]
        for stage in hypnogram.stages:
            saver[0].append({
                'epoch': stage['Epoch'],
                'start': stage['Epoch'] * epolen - epolen,
                'end':   stage['Epoch'] * epolen,
                'stage': stage['Stage'],
                'digit': stage['Digit'],
                'uncertain': stage['Uncertainty'],
                'channels': stage['Channels'],
                'clean': 0 if stage['Epoch'] in artefacts.epoch else 1
                })     
                            
        # Annotations
        markers = {
            container.label: container.borders
            for container in containers
        }
        saver.append([markers])

        # Save json file
        json.dump(saver, file, indent=1)    