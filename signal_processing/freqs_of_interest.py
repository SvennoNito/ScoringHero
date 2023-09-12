def freqs_of_interest(freqs, config):
    lower_limit = config[0]["Spectogram_limit_hz"][0]
    upper_limit = config[0]["Spectogram_limit_hz"][1]
    return (freqs >= lower_limit) & (freqs <= upper_limit)
