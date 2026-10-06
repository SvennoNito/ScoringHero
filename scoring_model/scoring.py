"""Scoring: the stage of every epoch of a recording (see GLOSSARY: Scoring, Stage, Epoch).

No Qt, no file I/O, no dialogs. Epochs are addressed by 0-based index (the same index
as `ui.this_epoch`). The stage name is the only stored stage value; the hypnogram digit
is derived from STAGE_DIGITS. Epoch number (1-based), start and end are never stored;
they are derived from the index and the epoch length (`time_span`, `to_records`).
"""

from numbers import Integral

# The only stage table. Unscored is None and has no digit.
STAGE_DIGITS = {"Wake": 1, "N1": -1, "N2": -2, "N3": -3, "REM": 0, "Inconclusive": 2}
UNSCORED = None


def stage_digit(stage):
    """Hypnogram digit of a stage name; None for unscored."""
    return STAGE_DIGITS[stage] if stage is not None else None


class Scoring:
    """Stage, source, confidence, channels and clean flag of `n_epochs` epochs of
    `epoch_length_s` seconds. Starts fully unscored."""

    def __init__(self, n_epochs, epoch_length_s):
        self.epoch_length_s = epoch_length_s
        self._stage = [UNSCORED] * n_epochs
        self._source = [None] * n_epochs
        self._confidence = [None] * n_epochs
        self._channels = [[] for _ in range(n_epochs)]
        self._clean = [1] * n_epochs

    def __len__(self):
        return len(self._stage)

    # ---- per-epoch getters -------------------------------------------------

    def stage(self, epoch):
        return self._stage[self._check(epoch)]

    def digit(self, epoch):
        return stage_digit(self.stage(epoch))

    def source(self, epoch):
        return self._source[self._check(epoch)]

    def confidence(self, epoch):
        return self._confidence[self._check(epoch)]

    def channels(self, epoch):
        return list(self._channels[self._check(epoch)])

    def clean(self, epoch):
        return self._clean[self._check(epoch)]

    def stages(self):
        """Stage names of all epochs (copy)."""
        return list(self._stage)

    def time_span(self, epoch):
        """(start, end) in seconds of the 0-based epoch index: (i*L, (i+1)*L).
        The 1-based epoch number in the scoring file is epoch + 1."""
        i = self._check(epoch)
        return i * self.epoch_length_s, (i + 1) * self.epoch_length_s

    # ---- setters -----------------------------------------------------------

    def set(self, epochs, stage, source=None, confidence=None, channels=()):
        """Set stage, source, confidence and channels of one epoch (int) or many
        (iterable of indices). `stage`, `source` and `confidence` are either one value
        for all epochs or a sequence with one value per epoch. `channels` is one list
        of channel names, copied to every epoch. A None stage clears the epoch: source,
        confidence and channels are reset whatever is passed (the clean flag is kept)."""
        idx = [self._check(i) for i in self._as_list(epochs)]
        stages = self._per_epoch(stage, len(idx))
        sources = self._per_epoch(source, len(idx))
        confs = self._per_epoch(confidence, len(idx))
        for s in stages:
            if s is not None and s not in STAGE_DIGITS:
                raise ValueError(f"Unknown stage: {s!r}")
        for i, s, src, conf in zip(idx, stages, sources, confs):
            self._stage[i] = s
            self._source[i] = src if s is not None else None
            self._confidence[i] = float(conf) if s is not None and conf is not None else None
            self._channels[i] = list(channels) if s is not None else []

    def set_clean(self, epochs, clean):
        """Set the clean flag (1 clean, 0 artefact) of one epoch or many."""
        for i in self._as_list(epochs):
            self._clean[self._check(i)] = int(bool(clean))

    # ---- records conversion ------------------------------------------------

    def to_records(self):
        """List of epoch records as stored in the ScoringHero scoring file. The digit is
        written next to the stage; epoch (1-based), start and end are computed."""
        records = []
        for i in range(len(self)):
            start, end = self.time_span(i)
            records.append({
                "epoch": i + 1,
                "start": start,
                "end": end,
                "stage": self._stage[i],
                "digit": stage_digit(self._stage[i]),
                "confidence": self._confidence[i],
                "channels": list(self._channels[i]),
                "clean": self._clean[i],
                "source": self._source[i],
            })
        return records

    @classmethod
    def from_records(cls, records, epoch_length_s, replace_unknown=False):
        """Scoring of len(records) epochs. The stored digit, epoch, start and end are
        ignored; the stage name wins. Stage names outside the table raise ValueError
        (see `unknown_stages`), or become unscored if `replace_unknown` is set."""
        if not replace_unknown:
            unknown = unknown_stages(records)
            if unknown:
                raise ValueError(f"Unknown stages: {unknown}")
        scoring = cls(len(records), epoch_length_s)
        for i, rec in enumerate(records):
            stage = rec.get("stage")
            if stage not in STAGE_DIGITS:
                continue  # unscored, or unknown replaced with unscored
            scoring.set(i, stage, rec.get("source"), rec.get("confidence"), rec.get("channels") or [])
            scoring._clean[i] = int(rec.get("clean", 1))
        return scoring

    # ---- length fitting ----------------------------------------------------

    def fitted(self, n_epochs):
        """New Scoring of exactly `n_epochs`: longer is truncated (so +1 drops the last
        epoch); shorter repeats the last epoch (stage, source and confidence; channels
        empty, clean) until the length matches. This is the only way to get a scoring of
        the recording's epoch count from a foreign length."""
        out = Scoring(n_epochs, self.epoch_length_s)
        for i in range(min(n_epochs, len(self))):
            out._stage[i] = self._stage[i]
            out._source[i] = self._source[i]
            out._confidence[i] = self._confidence[i]
            out._channels[i] = list(self._channels[i])
            out._clean[i] = self._clean[i]
        if len(self) and n_epochs > len(self):
            last = len(self) - 1
            for i in range(len(self), n_epochs):
                out._stage[i] = self._stage[last]
                out._source[i] = self._source[last]
                out._confidence[i] = self._confidence[last]
        return out

    # ---- helpers -----------------------------------------------------------

    def _check(self, epoch):
        if not 0 <= epoch < len(self):
            raise IndexError(f"Epoch {epoch} out of range for {len(self)} epochs")
        return int(epoch)

    @staticmethod
    def _as_list(epochs):
        return [epochs] if isinstance(epochs, Integral) else list(epochs)

    @staticmethod
    def _per_epoch(value, n):
        if hasattr(value, "__len__") and not isinstance(value, str):
            if len(value) != n:
                raise ValueError(f"Expected {n} values, got {len(value)}")
            return list(value)
        return [value] * n


def unknown_stages(records):
    """Distinct stage names in records that are not in the stage table (unscored None
    excluded), sorted, as strings."""
    return sorted({str(r.get("stage")) for r in records
                   if r.get("stage") is not None and r.get("stage") not in STAGE_DIGITS})
