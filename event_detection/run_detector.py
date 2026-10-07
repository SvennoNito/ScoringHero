"""Run an Event detector on one channel. No Qt, no `ui`: the GUI function passes the
settings, the displayed signal rows, the channel names, the sampling rate and the
primary Scoring; this returns the detected events as [start, end] seconds, restricted to
the chosen stages when there are any.

An Event detector is described by a `DetectorSpec`. Its detect function may raise
`DetectorUnavailable` (missing library or model) with the hint to show the user; any
other exception propagates unchanged."""

from dataclasses import dataclass
from typing import Callable

import numpy as np


class DetectorUnavailable(Exception):
    """A detector cannot run here (library or model missing). `title` and `message`
    are shown to the user as they are."""

    def __init__(self, title, message):
        super().__init__(message)
        self.title = title
        self.message = message


@dataclass(frozen=True)
class DetectorSpec:
    detect: Callable    # detect(signal_1d_float64, sfreq, **args(settings)) -> [[start_s, end_s], ...]
    args: Callable      # settings -> keyword arguments for `detect`
    method: str         # "MT-KCD": error dialog title is "<method> Error"
    title: str          # progress dialog title
    noun: str           # "KC": "Done — N KC(s) detected."


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


def run_detector(spec, settings, signals, channel_names, sfreq, scoring):
    """Detect events on `settings["channel"]`; raises ValueError if no such channel."""
    channel = settings["channel"]
    if channel not in channel_names:
        raise ValueError(f"Channel '{channel}' not found.")
    signal = np.asarray(signals[channel_names.index(channel)], dtype=np.float64).copy()
    events_sec = spec.detect(signal, sfreq, **spec.args(settings))
    stages = settings.get("filter_stages")
    if stages:
        events_sec = events_in_stages(scoring, events_sec, stages)
    return events_sec
