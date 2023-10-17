from .draw_event_in_this_epoch import draw_event_in_this_epoch
from scoring.write_scoring import write_scoring
from scoring.clean_epochs_to_uistages import clean_epochs_to_uiscoring

def drop_event(ui, converted_corners):
    for container in ui.AnnotationContainer:
        for index, border in enumerate(container.borders):
            if border[0] <= converted_corners[0].x() <= border[1]:
                container.borders.pop(index)
                container.epochs.pop(index)

        # Update clean epochs in scoring structure
        clean_epochs_to_uiscoring(ui, container)                

        # Draw rectangle
        draw_event_in_this_epoch(ui, container)

    # Write scoring file
    write_scoring(ui)
