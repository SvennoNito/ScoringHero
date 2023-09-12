import pickle

def write_cache(ui, cache):
    with open(f"{ui.filename}.cache.pkl", "wb") as file:
        pickle.dump(cache, file)    