def ui_to_cache(ui, cache={}):
    cache["spectogram"] = {}
    cache["spectogram"]["power"] = ui.power
    cache["spectogram"]["freqs"] = ui.freqs
    cache["spectogram"]["freqsOI"] = ui.freqsOI
    cache["spectogram"]["swa"] = ui.swa

    cache["Sampling_rate_hz"] = ui.config[0]["Sampling_rate_hz"]
    cache["Epoch_length_s"] = ui.config[0]["Epoch_length_s"]
    cache["Channel_for_spectogram"] = ui.config[0]["Channel_for_spectogram"]
    return cache
