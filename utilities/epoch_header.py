"""Text shown in the epoch header above the EEG panel."""

from pathlib import Path

import numpy as np

MAX_NAME_LENGTH = 20


def comparison_display_name(path):
    """File stem of the comparison scoring, cut to MAX_NAME_LENGTH characters ending in '…'."""
    stem = Path(path).stem
    if len(stem) > MAX_NAME_LENGTH:
        return stem[: MAX_NAME_LENGTH - 1] + "…"
    return stem


def epoch_header_text(this_epoch, numepo, stages, stages_comparison=None, comparison_name=None):
    """HTML header: epoch, primary stage, comparison stage labelled by comparison_name
    (red on disagreement, black on agreement) and confidence."""
    stage = stages[this_epoch]["stage"]

    conf = stages[this_epoch]["confidence"]
    if conf is None:
        confidence_text = ""
    elif conf == 0:
        confidence_text = "(not sure)"
    else:
        confidence_text = f"| Confidence {np.round(conf * 100, 2)}%"

    if stages_comparison is None or this_epoch >= len(stages_comparison):
        return f"Epoch {this_epoch+1}/{numepo} | {stage} {confidence_text}"
    comparison_stage = stages_comparison[this_epoch]["stage"]
    color = "red" if stage != comparison_stage else "black"
    comparison_span = f'<span style="color:{color};">({comparison_name}: {comparison_stage})</span>'
    return f"Epoch {this_epoch+1}/{numepo} | {stage} {comparison_span} {confidence_text}"
