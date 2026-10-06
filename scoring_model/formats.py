"""Scoring file formats: one table of label, file filter, loader and writer.

No Qt, no dialogs. A loader takes a path and returns `Loaded`: stage names at the
file's native length (UNSCORED = None) plus optional per-epoch confidence, source,
channels, clean flag, and format-specific annotations. Rows or stage names it cannot
map become unscored epochs and are listed in `Loaded.unrecognised` for the caller to
report. Loaders raise on failure (missing file, unreadable content). Each format keeps
only its own code <-> stage-name map; hypnogram digits live in scoring.py. A writer
takes (scoring, path).

Length fitting and the cancel/replace choice stay with the caller (Scoring.fitted).
"""

import csv
import json
from dataclasses import dataclass, field

from .scoring import STAGE_DIGITS, UNSCORED, Scoring, unknown_stages


@dataclass
class Loaded:
    stages: list
    confidence: list = None  # per epoch, or None if the format has none
    source: list = None  # per epoch (None for unscored), or None
    channels: list = None  # per epoch lists of channel names (ScoringHero only)
    clean: list = None  # per epoch 1/0 (ScoringHero only)
    annotations: list = field(default_factory=list)  # ScoringHero: events; Sleeptrip: per-epoch artefact column
    unrecognised: list = field(default_factory=list)  # unknown stage names / unparsable rows, in file order


def to_scoring(loaded, epoch_length_s):
    """Scoring of the file's native length from a Loaded result."""
    scoring = Scoring(len(loaded.stages), epoch_length_s)
    for i, stage in enumerate(loaded.stages):
        if stage is None:
            continue
        scoring.set(
            i,
            stage,
            loaded.source[i] if loaded.source else None,
            loaded.confidence[i] if loaded.confidence else None,
            loaded.channels[i] if loaded.channels else (),
        )
        if loaded.clean:
            scoring.set_clean(i, loaded.clean[i])
    return scoring


def _invert(table):
    return {stage: code for code, stage in table.items()}


def _source(stages, name):
    return [name if s is not None else None for s in stages]


# ---- ScoringHero (.json: [records, events]) -------------------------------------


def load_scoringhero(path):
    """Reads the stage records of the shared file; events are returned as annotations
    untouched. The stored digit is ignored: the stage name wins. Unknown stage names
    become unscored and are listed."""
    with open(path, "r") as file:
        records, events = json.load(file)
    unknown = unknown_stages(records)
    stages = [r.get("stage") if r.get("stage") in STAGE_DIGITS else UNSCORED for r in records]
    return Loaded(
        stages=stages,
        confidence=[r.get("confidence") for r in records],
        source=[r.get("source") if s is not None else None for r, s in zip(records, stages)],
        channels=[r.get("channels") or [] for r in records],
        clean=[int(r.get("clean", 1)) for r in records],
        annotations=events,
        unrecognised=unknown,
    )


def write_scoringhero(scoring, path, events=()):
    """Records conversion only: writes [to_records(), events] in the app's JSON layout.
    The caller owns the shared stage-and-event file and must pass the events to keep."""
    with open(path, "w") as file:
        json.dump([scoring.to_records(), list(events)], file, indent=1)


# ---- Zurich VIS (.vis) -----------------------------------------------------------

_VIS_STAGES = {"0": "Wake", "1": "N1", "2": "N2", "3": "N3", "r": "REM", "e": "Wake"}
_VIS_SYMBOLS = {"Wake": "0", "N1": "1", "N2": "2", "N3": "3", "REM": "r"}


def load_vis(path):
    """First line is an offset; then `<epoch number> <symbol> [comment]`. Epochs absent
    from the file are filled from the nearest scored epoch (forward, then backward); a
    final 'e' symbol repeats the previous one. Rows that do not parse, and symbols outside
    the map, are listed (unknown symbols become unscored)."""
    unrecognised = []
    rows = []  # (epoch number, symbol or UNKNOWN)
    with open(path, "r") as file:
        int(file.readline().strip())  # offset line
        for line in file:
            columns = line.strip().split()
            if not columns:
                continue
            try:
                if not 2 <= len(columns) <= 3:
                    raise ValueError
                rows.append((int(columns[0]), columns[1]))
            except ValueError:
                unrecognised.append(line.strip())
    if not rows:
        raise ValueError(f"No scored epochs in {path}")
    if rows[-1][1] == "e" and len(rows) > 1:
        rows[-1] = (rows[-1][0], rows[-2][1])

    unknown = object()  # distinguishes an unknown symbol from a gap
    filled = [None] * rows[-1][0]
    for epoch, symbol in rows:
        if symbol in _VIS_STAGES:
            filled[epoch - 1] = _VIS_STAGES[symbol]
        else:
            filled[epoch - 1] = unknown
            unrecognised.append(symbol)
    for sweep in (range(len(filled)), range(len(filled) - 1, -1, -1)):
        last = None
        for i in sweep:
            if filled[i] is not None:
                last = filled[i]
            elif last is not None:
                filled[i] = last
    stages = [UNSCORED if s is unknown else s for s in filled]
    return Loaded(stages=stages, unrecognised=unrecognised)


def write_vis(scoring, path):
    with open(path, "w") as f:
        f.write("0\n")  # offset line
        for i in range(len(scoring)):
            f.write(f"{i + 1} {_VIS_SYMBOLS.get(scoring.stage(i), '0')}\n")


# ---- YASA (.txt) -----------------------------------------------------------------

_YASA_STAGES = {
    "W": "Wake", "WAKE": "Wake", "0": "Wake",
    "N1": "N1", "NREM1": "N1", "1": "N1",
    "N2": "N2", "NREM2": "N2", "2": "N2",
    "N3": "N3", "NREM3": "N3", "3": "N3",
    "R": "REM", "REM": "REM", "4": "REM",
}
_YASA_LABELS = {"Wake": "W", "N1": "N1", "N2": "N2", "N3": "N3", "REM": "R"}


def load_yasa(path):
    """One stage code per line, case-insensitive. Non-matching lines are skipped."""
    with open(path, "r") as file:
        lines = file.readlines()
    stages = []
    for line in lines:
        stage = _YASA_STAGES.get(line.strip().upper())
        if stage is not None:
            stages.append(stage)
    return Loaded(stages=stages)


def write_yasa(scoring, path):
    with open(path, "w") as f:
        for i in range(len(scoring)):
            f.write(f"{_YASA_LABELS.get(scoring.stage(i), '')}\n")


# ---- Sleeptrip (.csv: stage code, artefact flag) ---------------------------------

_SLEEPTRIP_STAGES = {"0": "Wake", "1": "N1", "2": "N2", "3": "N3", "5": "REM"}
_SLEEPTRIP_CODES = _invert(_SLEEPTRIP_STAGES)


def load_sleeptrip(path):
    """First column is the stage code; rows whose first column is not a code are
    skipped. Annotations: the second column of every row as an int (0 if absent or not
    a number), the per-epoch artefact flag."""
    with open(path, "r", newline="") as csvfile:
        all_lines = list(csv.reader(csvfile))
    stages = [
        _SLEEPTRIP_STAGES[row[0]] for row in all_lines if row and row[0] in _SLEEPTRIP_STAGES
    ]
    annotations = []
    if any(len(row) >= 2 for row in all_lines):
        for row in all_lines:
            try:
                annotations.append(int(row[1]))
            except (ValueError, IndexError):
                annotations.append(0)
    return Loaded(stages=stages, source=_source(stages, "Sleeptrip"), annotations=annotations)


def write_sleeptrip(scoring, path):
    with open(path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for i in range(len(scoring)):
            digit = _SLEEPTRIP_CODES.get(scoring.stage(i), "")
            writer.writerow([digit, 0 if scoring.clean(i) else 1])


# ---- Sleepyland (.annot, tab separated) ------------------------------------------

_SLEEPYLAND_STAGES = {"W": "Wake", "N1": "N1", "N2": "N2", "N3": "N3", "R": "REM"}
_SLEEPYLAND_KEYS = _invert(_SLEEPYLAND_STAGES)
_SLEEPYLAND_CONF = {"Wake": "pW", "N1": "pN1", "N2": "pN2", "N3": "pN3", "REM": "pR"}


def load_sleepyland(path):
    """Header, then `epoch, stage, start, end, duration, meta` per row. Confidence is the
    meta probability of the epoch's stage. Short rows and unknown stage codes become
    unscored epochs and are listed."""
    stages, confidence, unrecognised = [], [], []
    with open(path, "r") as file:
        next(file)  # header
        for line in file:
            if not line.strip():
                continue
            parts = line.strip().split("\t")
            if len(parts) < 6:
                stages.append(UNSCORED)
                confidence.append(None)
                unrecognised.append(line.strip())
                continue
            stage = _SLEEPYLAND_STAGES.get(parts[1].strip())
            if stage is None:
                stages.append(UNSCORED)
                confidence.append(None)
                unrecognised.append(parts[1].strip())
                continue
            conf = {}
            for item in parts[5].strip().split(";"):
                if "=" in item:
                    k, v = item.split("=")
                    conf[k.strip()] = float(v.strip())
            stages.append(stage)
            confidence.append(conf.get(_SLEEPYLAND_CONF[stage]))
    return Loaded(
        stages=stages,
        confidence=confidence,
        source=_source(stages, "Sleepyland"),
        unrecognised=unrecognised,
    )


def _sleepyland_meta(stage, confidence):
    value = confidence if confidence is not None else 1.0
    active = _SLEEPYLAND_CONF.get(stage)
    return "; ".join(
        f"{k}={value if k == active else 0.0}" for k in ["pW", "pN1", "pN2", "pN3", "pR"]
    )


def write_sleepyland(scoring, path):
    epolen = scoring.epoch_length_s
    with open(path, "w") as f:
        f.write("Epoch\tStage\tStart\tEnd\tDuration\tMeta\n")
        for i in range(len(scoring)):
            stage = scoring.stage(i)
            key = _SLEEPYLAND_KEYS.get(stage, "W")
            start, end = scoring.time_span(i)
            meta = _sleepyland_meta(stage, scoring.confidence(i))
            f.write(f"{i + 1}\t{key}\t{start}\t{end}\t{epolen}\t{meta}\n")


# ---- GSSC (.csv) -----------------------------------------------------------------

_GSSC_STAGES = {0: "Wake", 1: "N1", 2: "N2", 3: "N3", 4: "REM"}
_GSSC_CODES = _invert(_GSSC_STAGES)


def load_gssc(path):
    """Header, then `epoch, start, stage code, pWake, pN1, pN2, pN3, pREM`. Confidence is
    the probability of the epoch's stage. Unknown codes and unparsable rows become
    unscored epochs and are listed."""
    stages, confidence, unrecognised = [], [], []
    with open(path, "r") as file:
        next(file)  # header
        for line in file:
            if not line.strip():
                continue
            parts = line.strip().split(",")
            if parts[0] == "Epoch":
                continue
            try:
                code = int(parts[2])
                stage = _GSSC_STAGES[code]
                conf = float(parts[3 + code])
            except (ValueError, KeyError, IndexError):
                stages.append(UNSCORED)
                confidence.append(None)
                unrecognised.append(line.strip())
                continue
            stages.append(stage)
            confidence.append(conf)
    return Loaded(
        stages=stages,
        confidence=confidence,
        source=_source(stages, "GSSC"),
        unrecognised=unrecognised,
    )


def write_gssc(scoring, path):
    epolen = scoring.epoch_length_s
    with open(path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Epoch", "Start", "Stage", "pWake", "pN1", "pN2", "pN3", "pREM"])
        for i in range(len(scoring)):
            code = _GSSC_CODES.get(scoring.stage(i), 0)
            confidence = scoring.confidence(i)
            value = confidence if confidence is not None else 1.0
            confs = [value if j == code else 0.0 for j in range(5)]
            writer.writerow([i + 1, i * epolen, code] + confs)


# ---- the table -------------------------------------------------------------------


@dataclass(frozen=True)
class Format:
    name: str
    label: str
    file_filter: str
    loader: object
    writer: object


FORMATS = {
    f.name: f
    for f in [
        Format("scoringhero", "ScoringHero (.json)", "*.json", load_scoringhero, write_scoringhero),
        Format("vis", "Zurich Scoring (.vis)", "*.vis", load_vis, write_vis),
        Format("yasa", "YASA (.txt)", "*.txt", load_yasa, write_yasa),
        Format("sleeptrip", "Sleeptrip (.csv)", "*.csv", load_sleeptrip, write_sleeptrip),
        Format("sleepyland", "Sleepyland (.annot)", "*.annot", load_sleepyland, write_sleepyland),
        Format(
            "gssc",
            "Greifswald Sleep Stage Classifier / GSSC (.csv)",
            "*.csv",
            load_gssc,
            write_gssc,
        ),
    ]
}
