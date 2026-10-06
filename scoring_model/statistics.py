"""Sleep statistics of a Scoring: numbers only, stage-only. Report text, options and
arousals (which depend on events) stay in the export.

Rules (as in the sleep report): sleep is N1, N2, N3 and REM. Inconclusive is neither
sleep nor wake but counts in the scored-epoch total (and so in the recording time).
Unscored epochs are not counted. Times are in minutes, efficiency in percent.
"""

from dataclasses import dataclass

from .scoring import STAGE_DIGITS

SLEEP_STAGES = ("N1", "N2", "N3", "REM")
# Awakenings are counted from these stages only (N1 -> Wake is not an awakening).
AWAKENING_FROM = ("N3", "N2", "REM")
LATENCY_STAGES = ("N2", "N3", "REM")


@dataclass(frozen=True)
class SleepStatistics:
    stage_counts: dict  # epochs per stage, every stage of the table (Inconclusive included)
    scored_epochs: int  # all scored epochs, Inconclusive included
    total_sleep_min: float
    total_recording_min: float  # scored epochs, not the whole recording
    efficiency: float  # total sleep / total recording * 100; 0 without scored epochs
    latency_min: dict  # N2/N3/REM: first epoch index of the stage * epoch length, None if absent
    awakenings: dict  # N3/N2/REM: awakenings by the stage before them
    awakening_durations_min: list  # one per awakening, in order


def sleep_statistics(scoring):
    stages = scoring.stages()
    epoch_min = scoring.epoch_length_s / 60

    stage_counts = {stage: stages.count(stage) for stage in STAGE_DIGITS}
    scored = [s for s in stages if s is not None]
    sleep_epochs = sum(stage_counts[s] for s in SLEEP_STAGES)
    total_sleep_min = sleep_epochs * epoch_min
    total_recording_min = len(scored) * epoch_min
    efficiency = total_sleep_min / total_recording_min * 100 if total_recording_min > 0 else 0.0

    # Latencies count from the recording start, unscored epochs included.
    latency_min = {s: stages.index(s) * epoch_min if s in stages else None for s in LATENCY_STAGES}

    # Awakenings use the scored epochs in order (unscored skipped) and only those
    # before the last epoch of N2/N3/REM; a Wake run is one awakening.
    last_sleep = max((i for i, s in enumerate(scored) if s in AWAKENING_FROM), default=None)
    awakenings = dict.fromkeys(AWAKENING_FROM, 0)
    durations = []
    if last_sleep is not None:
        i = 1
        while i < len(scored):
            prev = scored[i - 1]
            if scored[i] == "Wake" and prev in AWAKENING_FROM and i < last_sleep:
                awakenings[prev] += 1
                j = i
                while j < len(scored) and scored[j] == "Wake":
                    j += 1
                durations.append((j - i) * epoch_min)
                i = j
            else:
                i += 1

    return SleepStatistics(stage_counts, len(scored), total_sleep_min, total_recording_min,
                           efficiency, latency_min, awakenings, durations)
