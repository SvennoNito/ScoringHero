from .merge_events import merge_events
from .event_epoch import event_epoch
from .draw_event_in_this_epoch import draw_event_in_this_epoch
from .epoch_in_merged_event import epoch_in_merged_event
from paint_event.convert_to_seconds import convert_to_seconds
from scoring.write_scoring import write_scoring
from scoring.clean_epochs_to_uistages import clean_epochs_to_uiscoring


def event_handler(box_index, ui):
    # Extract respective container
    container = ui.AnnotationContainer[box_index]

    # Compute rectangle size in seconds and microvolt
    converted_corners, _ = convert_to_seconds(ui, ui.PaintEventWidget.stored_corners)

    if len(converted_corners) == 0:
        # No rectangle was drawn
        converted_corners = [
            int(ui.this_epoch) * ui.config[0]["Epoch_length_s"],
            (int(ui.this_epoch) + 1) * ui.config[0]["Epoch_length_s"],
        ]

        # Append or remove epoch
        container.borders = epoch_in_merged_event(container.borders, converted_corners)
        if converted_corners not in container.borders:
            container.borders.append(converted_corners)
        else:
            container.borders.remove(converted_corners)

    else:
        # Rectangle was drawn
        [container.borders.append([corner[0].x(), corner[1].x()]) for corner in converted_corners]

    # Merge borders
    container.borders = merge_events(container.borders)

    # Associated epoch of each border
    container.epochs = event_epoch(container.borders, ui.config[0]["Epoch_length_s"], ui.numepo)

    # Update clean epochs in scoring structure
    clean_epochs_to_uiscoring(ui, container)

    # Draw rectangle
    draw_event_in_this_epoch(ui, container)

    # Update event in hypnogram
    ui.HypnogramWidget.draw_hypnogram(ui)

    # Update paint evenet
    ui.PaintEventWidget.reset()
    ui.SignalWidget.text_period.setText("")
    ui.SignalWidget.text_amplitude_signal.setText("")
    ui.SignalWidget.text_amplitude_box.setText("")

    # Write scoring file
    write_scoring(ui)
