import json, os
from PySide6.QtWidgets import QFileDialog


def write_scoring_popup(ui):
    name_of_scoringfile, _ = QFileDialog.getSaveFileName(
        None, "Write scoring file", ui.default_data_path, "*json"
    )
    ui.filename, _ = os.path.splitext(name_of_scoringfile)
    write_scoring_wrapper(ui)


def write_scoring_wrapper(ui):
    annotations = []
    for numerator, container in enumerate(ui.AnnotationContainer):
        for counter, (border, epochs) in enumerate(zip(container.borders, container.epochs)):
            annotations.append({
                'id': container.label,
                'id_number': numerator,
                'counter': counter,
                'epoch': epochs,
                'start': border[0],
                'end': border[1],
            })
    write_scoring(f"{ui.filename}.json", ui.stages, annotations)


def write_scoring(scoring_filename, stages, annotations):
    with open(scoring_filename, "w") as file:
        json.dump([stages, annotations], file, indent=1)
