from PySide6.QtWidgets import QMessageBox
from scoring_model.formats import write_scoringhero


def write_scoring(ui):
    try:
        annotations = []
        for numerator, container in enumerate(ui.AnnotationContainer):
            for counter, (border, epochs) in enumerate(zip(container.borders, container.epochs)):
                annotations.append(
                    {
                        "key": container.key,
                        "event": container.label,
                        "digit": numerator,
                        "counter": counter,
                        "epoch": epochs,
                        "start": border[0],
                        "end": border[1],
                    }
                )

        write_scoringhero(ui.scoring, f"{ui.filename}.json", annotations)

    except Exception as e:
        error_message = f"An error occurred while writing the scoring file in \n{ui.filename}.json: \n\n{str(e)} \n\nThis means that the latest change in the scoring file was not saved! Please 1) screenshot this errorbox and 2) go to the black command window that opened with this program and copy the last error messages. Please report this bug so that it can be fixed fast!"
        QMessageBox.critical(ui, "Error", error_message)
