"""Events: 13 Event slots with derived Event epochs (see GLOSSARY: Event, Event slot,
Event epochs).

No Qt, no drawing, no file I/O. A slot is identified by its position (0..N_SLOTS-1),
never by its label. Each slot has a label, a colour and an ordered, merged list of
[start, end] spans in seconds; slot 0 is the artefact slot. Event epochs are 0-based
epoch indices (the same index as `ui.this_epoch`), always derived from the spans and
the epoch grid (`set_grid`), never stored. Spans past the recording end are kept; only
their epochs are clipped to the epoch count.
"""

from math import ceil, floor

N_SLOTS = 13  # the only definition of the slot count
ARTEFACT_SLOT = 0

# RGBA, one per slot
SLOT_COLOURS = (
    (255, 200, 200, 75),
    (100, 149, 237, 100),
    (152, 251, 152, 100),
    (255, 255, 102, 100),
    (64, 224, 208, 100),
    (148, 103, 189, 100),
    (140, 86, 75, 100),
    (227, 119, 194, 100),
    (127, 127, 127, 100),
    (188, 189, 34, 100),
    (255, 165, 0, 100),
    (75, 0, 130, 100),
    (255, 105, 180, 100),
)
DEFAULT_LABELS = ("Artifact",) + tuple(f"F{slot}" for slot in range(1, N_SLOTS))

_EPS = 1e-6  # in epochs; absorbs float noise at epoch borders


class Events:
    """The events of every slot of a recording of `n_epochs` epochs of `epoch_length_s`
    seconds. Starts empty."""

    def __init__(self, epoch_length_s, n_epochs):
        self.epoch_length_s = epoch_length_s
        self.n_epochs = n_epochs
        self._labels = list(DEFAULT_LABELS)
        self._spans = [[] for _ in range(N_SLOTS)]

    def set_grid(self, epoch_length_s, n_epochs):
        """Tell the epoch grid again (new epoch length or recording). Events keep their times."""
        self.epoch_length_s = epoch_length_s
        self.n_epochs = n_epochs

    # ---- slot properties ---------------------------------------------------

    def label(self, slot):
        return self._labels[_check_slot(slot)]

    def set_label(self, slot, label):
        """Duplicate labels are allowed."""
        self._labels[_check_slot(slot)] = label

    def colour(self, slot):
        """RGBA tuple of the slot."""
        return SLOT_COLOURS[_check_slot(slot)]

    def spans(self, slot):
        """Ordered, merged [start, end] spans of the slot, in seconds (copy)."""
        return [list(span) for span in self._spans[_check_slot(slot)]]

    # ---- edits -------------------------------------------------------------

    def add(self, slot, spans):
        """Add (start, end) spans to the slot, merging overlapping and touching ones.
        Empty and reversed spans are ignored."""
        slot = _check_slot(slot)
        new = [[start, end] for start, end in spans if end > start]
        self._spans[slot] = _merge(self._spans[slot] + new)

    def toggle_epoch(self, slot, epoch):
        """Toggle the whole 0-based epoch in the slot: a fully covered epoch is removed
        (splitting a containing event), anything else is added (merging)."""
        slot = _check_slot(slot)
        if not 0 <= epoch < self.n_epochs:
            raise IndexError(f"Epoch {epoch} out of range for {self.n_epochs} epochs")
        start, end = epoch * self.epoch_length_s, (epoch + 1) * self.epoch_length_s
        if any(s <= start and end <= e for s, e in self._spans[slot]):
            self._spans[slot] = _clip(self._spans[slot], [(start, end)])
        else:
            self.add(slot, [(start, end)])

    def erase(self, ranges):
        """Clip (start, end) time ranges out of every slot. Empty ranges are ignored."""
        ranges = [(start, end) for start, end in ranges if end > start]
        self._spans = [_clip(spans, ranges) for spans in self._spans]

    def clear(self, slot):
        """Remove every event of the slot; the label stays."""
        self._spans[_check_slot(slot)] = []

    def relabel(self, time, target_slot):
        """Move the smallest event containing `time` (any slot) to `target_slot`, merging
        into it. Returns False if no event contains `time`."""
        target_slot = _check_slot(target_slot)
        found = [(end - start, slot, [start, end])
                 for slot, spans in enumerate(self._spans)
                 for start, end in spans if start <= time <= end]
        if not found:
            return False
        _, slot, span = min(found, key=lambda f: f[:2])
        self._spans[slot].remove(span)
        self.add(target_slot, [span])
        return True

    def drop(self, time):
        """Remove every event containing `time` in every slot. Returns how many were removed."""
        removed = 0
        for slot, spans in enumerate(self._spans):
            kept = [span for span in spans if not span[0] <= time <= span[1]]
            removed += len(spans) - len(kept)
            self._spans[slot] = kept
        return removed

    # ---- derived epochs and queries ----------------------------------------

    def epochs(self, slot):
        """0-based epochs overlapped by each event of the slot (one list per event, in
        the order of `spans`), clipped to the epoch count. A whole-epoch event refers to
        its own epoch only. An event past the recording end has an empty list."""
        return [self._epochs_of(start, end) for start, end in self._spans[_check_slot(slot)]]

    def covered_epochs(self, slot):
        """Set of 0-based epochs covered by any event of the slot."""
        return {epoch for epochs in self.epochs(slot) for epoch in epochs}

    def artefact_epochs(self):
        """Set of 0-based epochs covered by slot 0 (the epochs that count as unclean)."""
        return self.covered_epochs(ARTEFACT_SLOT)

    def events_in_epoch(self, epoch):
        """(slot, start, end) of every event overlapping the 0-based epoch, ordered by slot, then time."""
        return [(slot, start, end)
                for slot, spans in enumerate(self._spans)
                for (start, end), epochs in zip(spans, self.epochs(slot)) if epoch in epochs]

    def next_event_epoch(self, epoch):
        """Next 0-based epoch covered by any event, searching after `epoch` and wrapping
        around, ending with `epoch` itself (like the Scoring queries). None if no epoch has an event."""
        covered = set().union(*(self.covered_epochs(slot) for slot in range(N_SLOTS)))
        later = [e for e in covered if e > epoch]
        return min(later) if later else min(covered, default=None)

    def count(self, slot):
        """Number of events in the slot (includes events past the recording end)."""
        return len(self._spans[_check_slot(slot)])

    def total_duration(self, slot):
        """Total duration of the slot's events in seconds (includes events past the recording end)."""
        return sum(end - start for start, end in self._spans[_check_slot(slot)])

    def _epochs_of(self, start, end):
        first = max(floor(start / self.epoch_length_s + _EPS), 0)
        last = min(ceil(end / self.epoch_length_s - _EPS) - 1, self.n_epochs - 1)
        return list(range(first, last + 1))


def _check_slot(slot):
    if not 0 <= slot < N_SLOTS:
        raise IndexError(f"Event slot {slot} out of range for {N_SLOTS} slots")
    return int(slot)


def _merge(spans):
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def _clip(spans, ranges):
    """Spans with the (start, end) ranges cut out; pieces keep their order."""
    for r_start, r_end in ranges:
        pieces = []
        for start, end in spans:
            if end <= r_start or start >= r_end:
                pieces.append([start, end])
                continue
            if start < r_start:
                pieces.append([start, r_start])
            if end > r_end:
                pieces.append([r_end, end])
        spans = pieces
    return spans
