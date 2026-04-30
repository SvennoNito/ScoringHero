from .merge_events import merge_events
from .event_epoch import event_epoch
from .draw_event_in_this_epoch import draw_event_in_this_epoch
from scoring.write_scoring import write_scoring
from scoring.clean_epochs_to_uistages import clean_epochs_to_uiscoring


def relabel_event(ui, converted_corners, target_box_index):
    """Move an event at the click position to a different AnnotationContainer."""
    if target_box_index >= len(ui.AnnotationContainer):
        return False

    click_time = converted_corners[0].x()

    best_container = None
    best_index = None
    best_size = float('inf')
    for container in ui.AnnotationContainer:
        for index, border in enumerate(container.borders):
            if border[0] <= click_time <= border[1]:
                size = border[1] - border[0]
                if size < best_size:
                    best_size = size
                    best_container = container
                    best_index = index

    if best_container is None:
        return False

    border_to_move = best_container.borders.pop(best_index)
    best_container.epochs.pop(best_index)
    best_container.epochs_set.pop(best_index)
    clean_epochs_to_uiscoring(ui, best_container)
    draw_event_in_this_epoch(ui, best_container)

    target = ui.AnnotationContainer[target_box_index]
    target.borders.append(border_to_move)
    target.borders = merge_events(target.borders)
    target.epochs = event_epoch(
        target.borders, ui.config[0]["Epoch_length_s"], ui.numepo
    )
    target.epochs_set = [set(lst) for lst in target.epochs]
    clean_epochs_to_uiscoring(ui, target)
    draw_event_in_this_epoch(ui, target)

    ui.HypnogramWidget.update_hypnogram(ui)
    ui.HypnogramWidget.update_events(ui)

    write_scoring(ui)
    return True
