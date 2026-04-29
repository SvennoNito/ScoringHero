from .merge_events import merge_events
from .event_epoch import event_epoch
from .draw_event_in_this_epoch import draw_event_in_this_epoch
from scoring.clean_epochs_to_uistages import clean_epochs_to_uiscoring


def add_events_to_container(ui, events_sec, container):
    for start, end in events_sec:
        if end > start:
            container.borders.append([start, end])

    container.borders = merge_events(container.borders)
    container.epochs  = event_epoch(
        container.borders,
        ui.config[0]["Epoch_length_s"],
        ui.numepo,
    )
    clean_epochs_to_uiscoring(ui, container)
    draw_event_in_this_epoch(ui, container)
    ui.HypnogramWidget.update_hypnogram(ui)
    ui.HypnogramWidget.update_events(ui)
