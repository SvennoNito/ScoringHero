from .draw_box_in_epoch import draw_box_in_epoch
from scoring.write_scoring import write_scoring


def drop_event(ui, converted_corners):
    for container in ui.AnnotationContainer:
        for index, border in enumerate(container.borders):
            if border[0] <= converted_corners[0].x() <= border[1]:
                container.borders.pop(index)
                container.epochs.pop(index)

        # Draw rectangle
        draw_box_in_epoch(ui, container)

    # Write scoring file
    write_scoring(ui)
