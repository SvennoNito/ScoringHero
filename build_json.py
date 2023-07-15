import json

channel_data = [
    {"Channel": "F3",       "Color": "Black",   "Display": 1,   'Scale': 1},
    {"Channel": "F4",       "Color": "Black",   "Display": 0,   'Scale': 1},
    {"Channel": "C3",       "Color": "Black",   "Display": 1,   'Scale': 1},
    {"Channel": "C4",       "Color": "Black",   "Display": 0,   'Scale': 1},
    {"Channel": "P3",       "Color": "Black",   "Display": 1,   'Scale': 1},
    {"Channel": "P4",       "Color": "Black",   "Display": 0,   'Scale': 1},
    {"Channel": "EOG1",     "Color": "Blue",    "Display": 1,   'Scale': 1},
    {"Channel": "EOG2",     "Color": "Blue",    "Display": 1,   'Scale': 1},
    {"Channel": "Muscle",   "Color": "Magenta", "Display": 1,   'Scale': 1}
]

# Save channel data to a JSON file
with open("config.json", "w") as file:
    json.dump(channel_data, file, indent=4)