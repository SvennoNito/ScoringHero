from .merge_events import merge_events
from .event_epoch import event_epoch
from .draw_event_in_this_epoch import draw_event_in_this_epoch
from .epoch_in_merged_event import epoch_in_merged_event
from paint_event.convert_to_seconds import convert_to_seconds
from scoring.write_scoring import write_scoring


def event_handler(box_index, ui):
    # Extract respective container
    container = ui.AnnotationContainer[box_index]

    # Compute rectangle size in seconds and microvolt
    converted_corners, _ = convert_to_seconds(ui, ui.PaintEventWidget.stored_corners)

    if len(converted_corners) == 0:
        # No rectangle was drawn
        converted_corners = [
            ui.this_epoch * ui.config[0]["Epoch_length_s"],
            (ui.this_epoch + 1) * ui.config[0]["Epoch_length_s"],
        ]

        # Append or remove epoch
        container.borders = epoch_in_merged_event(container.borders, converted_corners)
        if converted_corners not in container.borders:
            container.borders.append(converted_corners)
        else:
            container.borders.remove(converted_corners)

    else:
        # Rectangle was drawn
        [
            container.borders.append([corner[0].x(), corner[1].x()])
            for corner in converted_corners
        ]

    # Merge borders
    container.borders = merge_events(container.borders)

    # Associated epoch of each border
    container.epochs = event_epoch(container.borders, ui.config[0]["Epoch_length_s"])

    # Draw rectangle
    draw_event_in_this_epoch(ui, container)

    # Update paint evenet
    ui.PaintEventWidget.reset()
    ui.SignalWidget.text_period.setText("")
    ui.SignalWidget.text_amplitude.setText("")

    # Write scoring file
    write_scoring(ui)
