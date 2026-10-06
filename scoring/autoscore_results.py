"""Autoscorer results into a Scoring. No Qt, no `ui`: the window code passes the primary
Scoring and the raw model output; the modes (overwrite / fill_missing / selective) are
resolved here, per epoch, against the scoring as it was before the run.

The models score 30 s epochs (`MODEL_EPOCH_S`). A Scoring epoch takes the model epoch
that contains its midpoint, the midpoint coming from `Scoring.time_span`."""

from .nidra_runner import CODE_TO_COLUMN

MODEL_EPOCH_S = 30

GSSC_STAGES = {0: "Wake", 1: "N1", 2: "N2", 3: "N3", 4: "REM"}

# NIDRA hypnogram codes. 4 is unused (where AASM once had N4); 6 = artifact, handled apart.
NIDRA_STAGES = {0: "Wake", 1: "N1", 2: "N2", 3: "N3", 5: "REM"}
NIDRA_ARTIFACT_CODE = 6

YASA_STAGES = {"W": "Wake", "R": "REM", "N1": "N1", "N2": "N2", "N3": "N3"}


def _targets(scoring, n_model_epochs, mode, overwrite_stages):
    """[(scoring epoch, model epoch)] to write: epochs the mode allows and whose
    midpoint lies inside the model output."""
    pairs = []
    for i in range(len(scoring)):
        stage = scoring.stage(i)
        if mode == "fill_missing" and stage is not None:
            continue
        if mode == "selective" and stage not in overwrite_stages:
            continue
        start, end = scoring.time_span(i)
        j = int(((start + end) / 2.0) // MODEL_EPOCH_S)
        if 0 <= j < n_model_epochs:
            pairs.append((i, j))
    return pairs


def apply_gssc(scoring, gssc_stages, probs, channels, mode="overwrite", overwrite_stages=None):
    """Write GSSC output (stage code per 30 s epoch, `probs` [n, 5] or None) into
    `scoring` with source "GSSC", the winning-class probability as confidence and
    `channels`. Returns the number of epochs written."""
    pairs = _targets(scoring, len(gssc_stages), mode, overwrite_stages)
    codes = [int(gssc_stages[j]) for _, j in pairs]
    confidence = [
        round(float(probs[j, code]), 4) if probs is not None and j < len(probs) else None
        for (_, j), code in zip(pairs, codes)
    ]
    scoring.set([i for i, _ in pairs], [GSSC_STAGES[c] for c in codes], "GSSC", confidence, channels)
    return len(pairs)


def apply_nidra(scoring, hypnogram, probabilities, class_names, source, channels,
                artifact_mode="unscored", store_probabilities=False,
                mode="overwrite", overwrite_stages=None):
    """Write NIDRA output (code per 30 s epoch, probabilities [n, classes]) into
    `scoring`. Artifact epochs (code 6) are marked unclean and get source
    "<source> — artifact"; their stage is Inconclusive if `artifact_mode` is
    "inconclusive", else unscored (source, confidence and channels are kept on the
    unscored epoch). Returns the [start, end] seconds of the artifact epochs."""
    pairs = _targets(scoring, len(hypnogram), mode, overwrite_stages)
    epochs, stages, sources, confidence, artifacts, probs = [], [], [], [], [], []
    for i, j in pairs:
        code = int(hypnogram[j])
        column = CODE_TO_COLUMN.get(code)
        confidence.append(
            round(float(probabilities[j, column]), 4)
            if column is not None and column < probabilities.shape[1] else None
        )
        if code == NIDRA_ARTIFACT_CODE:
            stages.append("Inconclusive" if artifact_mode == "inconclusive" else None)
            sources.append(f"{source} — artifact")
            artifacts.append(i)
        else:
            stages.append(NIDRA_STAGES[code])
            sources.append(source)
        probs.append(
            {name: round(float(probabilities[j, k]), 4) for k, name in enumerate(class_names)}
            if store_probabilities else None
        )
        epochs.append(i)
    scoring.set(epochs, stages, sources, confidence, channels, probs)
    scoring.set_clean(artifacts, 0)
    return [list(scoring.time_span(i)) for i in artifacts]


def apply_yasa(scoring, stages, confidence):
    """Write YASA staging output (names 'W', 'R', 'N1', 'N2', 'N3' per 30 s epoch and
    the winning-class probability) into `scoring` with source "YASA". Returns the
    number of epochs written."""
    pairs = _targets(scoring, len(stages), "overwrite", None)
    scoring.set(
        [i for i, _ in pairs],
        [YASA_STAGES[str(stages[j])] for _, j in pairs],
        "YASA",
        [round(float(confidence[j]), 4) for _, j in pairs],
    )
    return len(pairs)


def events_in_stages(scoring, events_sec, stages):
    """Events ([start, end] seconds) whose midpoint lies in an epoch scored as one of
    `stages`."""
    selected = set(stages)
    kept = []
    for start, end in events_sec:
        epoch = int(((start + end) / 2.0) / scoring.epoch_length_s)
        if epoch < len(scoring) and scoring.stage(epoch) in selected:
            kept.append([start, end])
    return kept
