"""Scoring the last epoch must refresh the epoch header and export-menu state."""

from scoring_model.scoring import Scoring
from utilities.score_stage import score_stage


def test_scoring_last_epoch_refreshes_header_and_export_menu(loaded_ui):
    ui = loaded_ui
    ui.scoring = Scoring(ui.numepo, ui.config[0]["Epoch_length_s"])
    ui.scoring_comparison = None
    ui.this_epoch = ui.numepo - 1
    ui.action_export_sleep_report.setEnabled(False)

    score_stage("N2", ui)

    assert ui.this_epoch == ui.numepo - 1
    assert f"Epoch {ui.numepo}/{ui.numepo} | N2" in ui.DisplayedEpochWidget.textfield.text()
    assert ui.action_export_sleep_report.isEnabled()
