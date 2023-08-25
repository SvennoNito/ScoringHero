import json

def write_to_cache(filename, values):
    with open(filename, "w") as file:
        json.dump(values, file, indent=1)  