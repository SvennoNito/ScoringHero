"""Caller-side resolution of a loaded scoring against the recording (same policy for
every format, including the ScoringHero file). No Qt: the user is reached through an
`ask` callback, so the decision logic is testable without dialogs.

Policy (length = loaded epochs - recording epochs):
  +1  tolerated with a notice, last (partial) epoch dropped
  +n  user chooses Cancel or "truncate"
  -1  tolerated with a notice, last epoch copied (stage, source, confidence)
  -n  user chooses Cancel or "copy_last" until the length matches
  unknown stages: user chooses Cancel or "replace" (with unscored)
Unknown stages are asked first, then length.

Cancel: `resolve` returns None. What cancel means is the caller's decision
(comparison import aborts; primary open continues with an empty scoring).
"""

from dataclasses import dataclass

from .formats import to_scoring


@dataclass(frozen=True)
class Problems:
    unknown: tuple  # distinct unrecognised stage names / rows, in file order
    diff: int  # loaded epochs - recording epochs

    @property
    def length_kind(self):
        if self.diff == 0:
            return "exact"
        return ("longer_" if self.diff > 0 else "shorter_") + ("1" if abs(self.diff) == 1 else "n")

    @property
    def tolerated(self):
        return abs(self.diff) == 1

    @property
    def length_choices(self):
        """Actions on offer besides Cancel; ("ok",) = notice only; () = no problem."""
        return {
            "exact": (),
            "longer_1": ("ok",),
            "shorter_1": ("ok",),
            "longer_n": ("truncate",),
            "shorter_n": ("copy_last",),
        }[self.length_kind]

    @property
    def unknown_choices(self):
        return ("replace",) if self.unknown else ()


@dataclass(frozen=True)
class Question:
    topic: str  # "unknown" or "length"
    kind: str  # length_kind for "length", "unknown" for "unknown"
    choices: tuple  # actions besides Cancel
    problems: Problems


def diagnose(loaded, n_epochs):
    unknown = tuple(dict.fromkeys(str(u) for u in loaded.unrecognised))
    return Problems(unknown, len(loaded.stages) - n_epochs)


def resolve(loaded, n_epochs, epoch_length_s, ask):
    """Scoring of exactly `n_epochs` from a `formats.Loaded`, or None if the user
    cancelled. `ask(Question)` returns one of question.choices, or None for Cancel."""
    problems = diagnose(loaded, n_epochs)
    if problems.unknown and ask(Question("unknown", "unknown", problems.unknown_choices, problems)) is None:
        return None
    if problems.length_choices and ask(Question("length", problems.length_kind, problems.length_choices, problems)) is None:
        return None
    # to_scoring already maps unrecognised stages to unscored; fitted truncates / copies last.
    return to_scoring(loaded, epoch_length_s).fitted(n_epochs)
