from .event_epoch import event_epoch
from scoring.clean_epochs_to_uistages import clean_epochs_to_uiscoring
from scoring.write_scoring import write_scoring
from utilities.refresh_gui import refresh_gui


def rebuild_event_epochs(ui, container):
    """Recompute the container's epoch lists, epoch sets and the scoring's clean
    epochs from its (edited) borders."""
    container.epochs = event_epoch(container.borders, ui.config[0]["Epoch_length_s"], ui.numepo)
    container.epochs_set = [set(lst) for lst in container.epochs]
    clean_epochs_to_uiscoring(ui, container)


def refresh_after_event_deletion(ui):
    """Write the scoring and refresh hypnogram stages, hypnogram events and the GUI."""
    write_scoring(ui)
    ui.HypnogramWidget.update_hypnogram(ui)
    ui.HypnogramWidget.update_events(ui)
    refresh_gui(ui)
