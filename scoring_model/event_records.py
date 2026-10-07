"""Event records: the conversion between Events and the event dicts of the ScoringHero
file, beside the Scoring record conversion (Scoring.to_records / from_records). No file
I/O, no dialogs.

A record is {key, event, digit, counter, epoch, start, end}: `event` is the slot label,
`digit` the slot, `counter` the position within the slot, `epoch` the 1-based epochs the
event overlaps, `start`/`end` seconds. Only `event`, `digit`, `start` and `end` are read
back; key, counter and epoch are derived on write and ignored on load. The sleeptrip
conversions return records for a chosen slot; the caller passes them to
`events_from_records` (or merges them into the file's records).
"""

from .events import N_SLOTS, Events, ARTEFACT_SLOT


def events_to_records(events):
    """Records of every event of every slot, ordered by slot, then time."""
    records = []
    for slot in range(N_SLOTS):
        for counter, ((start, end), epochs) in enumerate(zip(events.spans(slot), events.epochs(slot))):
            records.append({
                "key": _key(slot),
                "event": events.label(slot),
                "digit": slot,
                "counter": counter,
                "epoch": [epoch + 1 for epoch in epochs],
                "start": start,
                "end": end,
            })
    return records


def events_from_records(records, epoch_length_s, n_epochs):
    """Events from records; the slot is the digit, the slot label the record's event
    (the last record of a slot wins)."""
    events = Events(epoch_length_s, n_epochs)
    for record in records:
        slot = record["digit"]
        events.set_label(slot, record["event"])
        events.add(slot, [(record["start"], record["end"])])
    return events


def sleeptrip_event_records(raw_events, slot, label, epoch_length_s):
    """Records for the slot from sleeptrip events (dicts with `start` and `stop`, as
    returned by load_sleeptrip_events). The caller picks the events (mapping) to pass."""
    spans = [(raw["start"], raw["stop"]) for raw in raw_events]
    return _records_for(slot, label, spans, epoch_length_s, max((end for _, end in spans), default=0))


def artefact_flag_records(flags, slot, label, epoch_length_s):
    """Records for the slot from the sleeptrip per-epoch flags: one whole-epoch event per
    flagged epoch (a value of 1); neighbouring flagged epochs merge."""
    spans = [(i * epoch_length_s, (i + 1) * epoch_length_s) for i, flag in enumerate(flags) if flag == 1]
    return _records_for(slot, label, spans, epoch_length_s, len(flags) * epoch_length_s)


def _records_for(slot, label, spans, epoch_length_s, duration_s):
    events = Events(epoch_length_s, int(duration_s // epoch_length_s) + 1)
    events.set_label(slot, label)
    events.add(slot, spans)
    return events_to_records(events)


def _key(slot):
    return "A" if slot == ARTEFACT_SLOT else f"F{slot}"
