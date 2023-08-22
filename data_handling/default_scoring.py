def default_scoring(numepo, epolen):

    stages = []
    for counter in range(numepo):
        template = {
            "epoch": counter + 1,
            "start": counter * epolen,
            "end": (counter + 1) * epolen,
            "stage": None,
            "digit": None,
            "uncertain": 0,
            "channels": [],
            "clean": 1
        }
        stages.append(template)  
    return stages  