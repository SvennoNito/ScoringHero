import json, os

def write_json(mainbody, filename):
    # Function to save your work as json file

    if len(mainbody.scoringFile) > 0:
        with open(filename, mode='w', newline='') as file:

            # Sleep stages
            saver = [[]]
            for epoch, stage in mainbody.hypnogram.stages.items():
                saver[0].append({
                    'epoch': epoch,
                    'epoch start (s)': epoch * mainbody.epolen - mainbody.epolen,
                    'epoch end (s)': epoch * mainbody.epolen,
                    'sleep stage': stage[0],
                    'stage number': stage[1],
                    'clean epoch': 0 if epoch in mainbody.artefacts.epoch else 1
                    })     
                                
            # Annotations
            markers = {
                container.label: container.borders
                for container in mainbody.annotationAll
            }
            saver.append([markers])

            # Save json file
            json.dump(saver, file, indent=1)


def load_your_work(mainbody, scoring_file):
    # Function to load previously saved staging

    filename, extension = os.path.splitext(scoring_file)
    if extension == '.json':
        with open(f"{filename}.json", "r") as file:
            json_file = json.load(file)      

        # Load sleep stages
        for bucket in json_file[0]:
            mainbody.hypnogram.add_instance(bucket['epoch'], bucket['sleep stage'], bucket['stage number'])

        # Load annotations
        for container, label in zip(mainbody.containers, json_file[1][0].keys()):
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
        for container in mainbody.annotationAll:
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
            for container in mainbody.annotationAll:
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