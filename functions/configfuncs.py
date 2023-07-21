import os, json, re
import tkinter as tk 
import tkinter.simpledialog

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