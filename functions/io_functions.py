import json, os, re
import tkinter as tk 
import tkinter.simpledialog

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


def load_your_work(hypnogram, containers, scoring_file):
    # Function to load previously saved staging

    filename, extension = os.path.splitext(scoring_file)
    if extension == '.json':
        with open(f"{filename}.json", "r") as file:
            json_file = json.load(file)      

        # Load sleep stages
        for bucket in json_file[0]:
            hypnogram.assign(bucket['epoch'], bucket['stage'])

        # Load annotations
        for container, label in zip(containers, json_file[1][0].keys()):
            container.label     = label
            container.borders   = json_file[1][0][label]


def open_config(filename, EEG):
    if os.path.exists(f"{filename}.json"):
        with open(f"{filename}.json", "r") as file:
            config = json.load(file) # Open configuration file (.json)      

    else: # Create default configuration settings
        root = tk.Tk() 
        root.withdraw() 
        display_text    = "Configuration file «EEG_filename».json was not found. Loading default settings instead. \nIf you want to have more meaningful channel labels than «channel 1» or want to avoid this pop-up box, create a .json file named as your EEG file in the same folder as your EEG file. \nYou can use the function «build_json.py» for that or copy an existing .json file and adapt the values accordingly. \nTo continue for now, define the sampling rate of your data here (in Hz):"
        srate           = tk.simpledialog.askstring("Configuration file not found", display_text, parent=root)
        srate           = int(re.findall(r'\d+', srate)[0])
        # ctypes.windll.user32.MessageBoxW(0, "Configuration file «EEG_filename».json was not found. Loading default settings with a sampling rate of 125 Hz instead. If your data has a different sampling rate or you want to have more meaningful channel labels than «channel 1», create a .json file named as your EEG file in the same folder as your EEG file. You can use the function  «build_json.py» for that or copy an existing .json file and adapt the values accordingly.", "No configuration file found", 1)
        config = default_config(srate, EEG.data.shape[0])
    EEG.add_info(config[0])
    EEG.add_chaninfo(config[1])      
      

def default_config(srate, numchans):
    # Create default configuration settings when no json file is loaded

    config      = [[] for x in range(2)]
    config[0]   = {'SamplingRate': srate}
    for chan in range(numchans):
        if chan < 9:
            display = 1
        else:
            display = 0
        config[1].append({
            "Channel": f'Channel {chan+1}',
            "Color": "Black",
            "Display": display,
            "Scale": 1
        })
    return config            





























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