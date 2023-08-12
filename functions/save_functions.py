
import json, os, re, random, sys
import tkinter as tk 
import tkinter.simpledialog
import eeg_and_config_functions







def write_json(filename, epolen, hypnogram, artefacts, containers):
    # Function to save your work as json file

    with open(filename, mode='w', newline='') as file:
        if not filename.endswith(".json"):
            filename = f'{filename}.json'

        # Sleep stages
        saver = [[]]
        for stage in hypnogram.stages:
            saver[0].append({
                'epoch': stage['Epoch'],
                'start': stage['Epoch'] * epolen - epolen,
                'end':   stage['Epoch'] * epolen,
                'stage': stage['Stage'],
                'digit': stage['Digit'],
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

def choose_random(files, allow_existence=1):
    rand_index      = random.randint(0, len(files[0]) - 1)
    file            = files[0][rand_index]
    basename        = os.path.splitext(file)[0]
    scoring_file    = f'{basename}.json'
    if allow_existence == 0:
        while os.path.exists(scoring_file):
            rand_index      = random.randint(0, len(files[0]) - 1)
            file            = files[0][rand_index]
            scoring_file    = f'{os.path.splitext(file)[0]}.json'    
    
    data = open_eeg(file)
    return data, scoring_file, basename


def open_eeg(file):
    filename, extension = os.path.splitext(file)
    if extension == '.mat':
        if scipy.io.matlab.miobase.get_matfile_version(filename)[0] == 2: #v7.3 files
            with h5py.File(filename, "r") as file:
                data = file['EEG']['data'][:]
                if data.shape[0] > data.shape[1]: # dimensions are weird ....
                    data = data.T
        else:
            data = scipy.io.loadmat(filename)['EEG']['data'][0][0]
            # self.EEG.srate = scipy.io.loadmat(EEG_file)['EEG']['srate'][0][0][0][0] 
    return data, filename
    

def choose_random(files, allow_existence=1):
    rand_index      = random.randint(0, len(files[0]) - 1)
    file            = files[0][rand_index]
    basename        = os.path.splitext(file)[0]
    scoring_file    = f'{basename}.json'
    if allow_existence == 0:
        while os.path.exists(scoring_file):
            rand_index      = random.randint(0, len(files[0]) - 1)
            file            = files[0][rand_index]
            scoring_file    = f'{os.path.splitext(file)[0]}.json'    
    
    data = eeg_and_config_functions.load_eeg_and_configuration_settings(file)
    return data, scoring_file, basename


def load_your_work(hypnogram, containers, scoring_file):
    # Function to load previously saved staging

    filename, extension = os.path.splitext(scoring_file)
    if extension == '.json':
        if os.path.exists(scoring_file):
            with open(scoring_file, "r") as file:
                json_file = json.load(file)      

            # Load sleep stages
            for bucket in json_file[0]:
                hypnogram.assign(bucket['epoch'], bucket['stage'], bucket['channels'])

            # Load annotations
            for container, label in zip(containers, json_file[1][0].keys()):
                container.label     = label
                container.borders   = json_file[1][0][label]





























""" if extension == '.csv':
with open(scoring_file, mode='r') as file:

    reader = csv.reader(file)
    header = next(reader)
    reader = csv.DictReader(file, fieldnames = header)
    for count, container in enumerate(self.containers):
        container.label = header[count+6]
    for row in reader:
        self.hypnogram.assign_stage(int(row['epoch']), row['sleep stage'])
        for container in self.containers:
            container.add_instance(ast.literal_eval(row[container.label]))    """  


""" import csv
def write_csv(mainbody, filename):

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)     
        header = ['epoch', 'epoch start (s)', 'epoch end (s)', 'sleep stage', 'stage number', 'clean epoch']
        for container in mainbody.containers:
            header.append(container.label)                
        writer.writerows([header])
        for epoch, stage in mainbody.hypnogram.stages.items():
            epostart    = epoch*mainbody.epolen-mainbody.epolen
            epostop     = epoch*mainbody.epolen
            stagestr    = stage[0]
            stagenum    = stage[1]
            clean       = 1
            datawrite   = [epoch, epostart, epostop, stagestr, stagenum, clean]
            if epoch in mainbody.artefacts.epoch:
                datawrite[-1] = 0
            for container in mainbody.containers:
                if epoch in container.epoch:
                    e   = np.array(container.epoch)
                    b   = np.array(container.borders)
                    datawrite.append(b[e == epoch])
                else:
                    datawrite.append('-')
            for item in datawrite:
                if type(item) == np.ndarray:
                    item = [f'{i[0]}, {i[1]}' for i in item]
                    print(str(item))
            datawrite = [str(item) for item in datawrite]
            datawrite = [item.replace("\n", ",") for item in datawrite]
            datawrite = [re.sub(r'(?<=\d)\s+(?=\d)', ', ', item) for item in datawrite]
            writer.writerows([datawrite])   """   