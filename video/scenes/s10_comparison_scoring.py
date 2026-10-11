"""Scene 10: import a Comparison scoring, show the comparison summary statistics, then remove it."""

import copy
import os
from unittest import mock

import numpy as np
from PySide6.QtWidgets import QDialog

from scoring import scoring_import_comparison as import_module
from scoring_model.formats import FORMATS, write_scoringhero
from scoring_model.scoring import STAGES

CHANGED_FRACTION = 0.15  # share of epochs the second scorer disagrees on


def make_comparison_file(ctx):
    """ScoringHero scoring JSON off camera: the Primary scoring as it is now, with ~15% of the
    epochs given a different stage."""
    scoring = copy.deepcopy(ctx.ui.scoring)
    rng = np.random.default_rng(0)
    n = len(scoring)
    changed = sorted(rng.choice(n, size=round(CHANGED_FRACTION * n), replace=False).tolist())
    for epoch in changed:
        others = [s for s in STAGES if s != scoring.stage(epoch)]
        scoring.set(epoch, others[rng.integers(len(others))], source="human")
    path = os.path.join(ctx.video_dir, "comparison_scoring.json")
    write_scoringhero(scoring, path, [])
    ctx.state["s10_changed"] = len(changed)
    return path


def run(ctx):
    ui = ctx.ui
    ctx.wait_until(lambda: not getattr(ui, "_busy_runners", None))
    ctx.state["s10_path"] = path = make_comparison_file(ctx)
    ctx.caption("Import a Comparison scoring from a second scorer")
    # the format dialog is modal: answer it with the default format (ScoringHero .json)
    assert list(FORMATS.values())[0].file_filter == "*.json", "default import format is not ScoringHero JSON"
    with ctx.file_dialogs(open=path), mock.patch.object(import_module._FormatDialog, "exec", lambda self: True):
        ctx.click_menu("action_import_comparison")
    ctx.wait_until(lambda: ui.scoring_comparison is not None)
    ctx.state["s10_set"] = ui.scoring_comparison is not None and ui.action_comparison_stats.isEnabled()
    ctx.wait(2.0)

    ctx.caption("Show the summary statistics: agreement, Cohen's kappa and confusion matrix")
    dialogs = []

    def show_nonmodal(self):
        dialogs.append(self)
        self.show()
        return 0

    with mock.patch.object(QDialog, "exec", show_nonmodal):
        ctx.click_menu("action_comparison_stats")
    ctx.state["s10_stats_shown"] = bool(dialogs) and dialogs[0].isVisible()
    ctx.wait(4.0)
    for dialog in dialogs:
        dialog.close()
    ctx.wait(0.8)

    ctx.caption("Remove the Comparison scoring again")
    ctx.click_menu("action_remove_comparison")
    ctx.wait(1.5)
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    assert os.path.exists(ctx.state["s10_path"]), "comparison file was not generated"
    assert ctx.state["s10_changed"] > 0, "no epochs were changed in the comparison scoring"
    assert ctx.state["s10_set"], "Comparison scoring was not imported"
    assert ctx.state["s10_stats_shown"], "summary statistics were not shown"
    assert ui.scoring_comparison is None, "Comparison scoring was not removed"
    assert not ui.action_comparison_stats.isEnabled(), "comparison statistics still enabled"
