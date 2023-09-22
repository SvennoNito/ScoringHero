def load_r09(filename_prefix):
    with open(f'{filename_prefix}.r09', 'rb') as file:
        data = file.read()
    srate = 128
    return data, srate