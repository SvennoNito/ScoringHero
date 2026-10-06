"""Scoring the last epoch must refresh the epoch header and export-menu state."""

import time

from PySide6 import QtWidgets

from scoring_model.scoring import Scoring
from utilities.score_stage import score_stage


def _wait_until_loaded(ui, timeout_s=60):
    """The recording's analysis data is built on a worker thread after loading."""
    end = time.time() + timeout_s
    while not hasattr(ui.HypnogramWidget, "times") and time.time() < end:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.01)
    assert hasattr(ui.HypnogramWidget, "times"), "recording did not finish loading"


def test_scoring_last_epoch_refreshes_header_and_export_menu(boot_scoring, loaded_ui):
    ui = loaded_ui
    _wait_until_loaded(ui)
    ui.scoring = Scoring(ui.numepo, ui.config[0]["Epoch_length_s"])
    ui.scoring_comparison = None
    ui.this_epoch = ui.numepo - 1
    ui.action_export_sleep_report.setEnabled(False)

    score_stage("N2", ui)

    assert ui.this_epoch == ui.numepo - 1
    assert f"Epoch {ui.numepo}/{ui.numepo} | N2" in ui.DisplayedEpochWidget.textfield.text()
    assert ui.action_export_sleep_report.isEnabled()
