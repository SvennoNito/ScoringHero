"""What the status bar says about the displayed epoch."""

from pathlib import Path
from typing import NamedTuple, Optional

from .clock_time_format import format_clock_time_hms, parse_start_time

MAX_NAME_LENGTH = 20


def comparison_display_name(path):
    """File stem of the comparison scoring, cut to MAX_NAME_LENGTH characters ending in '…'."""
    stem = Path(path).stem
    if len(stem) > MAX_NAME_LENGTH:
        return stem[: MAX_NAME_LENGTH - 1] + "…"
    return stem


class EpochStatus(NamedTuple):
    stage: str
    confidence: str
    comparison: Optional[str]  # "scorer2: N3"; None without a comparison covering this epoch
    disagrees: bool
    clock: str


def epoch_status(ui):
    """Status of epoch `ui.this_epoch`: stage (Unscored when it has none), confidence
    ("Not sure" at 0, "—" when it has none), the comparison scoring's stage labelled by
    its name, and the clock time the epoch starts at."""
    epoch, scoring = ui.this_epoch, ui.scoring
    stage = scoring.stage(epoch)
    confidence = scoring.confidence(epoch)
    if confidence is None:
        confidence_text = "Confidence —"
    elif confidence == 0:
        confidence_text = "Not sure"
    else:
        confidence_text = f"Confidence {confidence * 100:.0f}%"

    comparison, disagrees = None, False
    other = ui.scoring_comparison
    if other is not None and epoch < len(other):
        other_stage = other.stage(epoch)
        comparison = f"{ui.comparison_name}: {'Unscored' if other_stage is None else other_stage}"
        disagrees = other_stage != stage

    start_s = parse_start_time(ui.config[0].get("Recording_start_time", "00:00"))
    clock = format_clock_time_hms(start_s + epoch * ui.config[0]["Epoch_length_s"])
    return EpochStatus("Unscored" if stage is None else stage, confidence_text, comparison, disagrees, clock)
