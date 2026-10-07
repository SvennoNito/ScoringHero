from scoring_model.event_records import events_to_records
from scoring_model.formats import write_scoringhero


def write_scoring(scoring, events, path):
    """Write the shared stage-and-event file. Raises on failure; the GUI reports it."""
    write_scoringhero(scoring, path, events_to_records(events))
