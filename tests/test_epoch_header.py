"""Tests for the epoch header text and the comparison scoring's display name."""

from scoring_model.scoring import Scoring
from utilities.epoch_header import comparison_display_name, epoch_header_text


def _stages(*names):
    scoring = Scoring(len(names), 30)
    for i, name in enumerate(names):
        scoring.set(i, name)
    return scoring


def test_no_comparison_loaded():
    text = epoch_header_text(1, 900, _stages("N1", "N2"))
    assert text == "Epoch 2/900 | N2 "


def test_disagreement_labels_comparison_stage_red_with_its_name():
    text = epoch_header_text(1, 900, _stages("N1", "N2"), _stages("N1", "N3"), "scorer2")
    assert text == 'Epoch 2/900 | N2 <span style="color:red;">(scorer2: N3)</span> '


def test_agreement_labels_comparison_stage_black():
    text = epoch_header_text(0, 900, _stages("N1", "N2"), _stages("N1", "N3"), "scorer2")
    assert text == 'Epoch 1/900 | N1 <span style="color:black;">(scorer2: N1)</span> '


def test_epoch_beyond_end_of_comparison_shows_no_comparison_label():
    text = epoch_header_text(1, 900, _stages("N1", "N2"), _stages("N1"), "scorer2")
    assert text == "Epoch 2/900 | N2 "


def test_display_name_drops_folder_and_extension():
    assert comparison_display_name("C:/data/night1/scorer2.txt") == "scorer2"


def test_display_name_keeps_20_character_stem():
    assert comparison_display_name("abcdefghijklmnopqrst.json") == "abcdefghijklmnopqrst"


def test_display_name_cuts_long_stem_with_ellipsis():
    name = comparison_display_name("subject042_night1_scorerB_final.csv")
    assert name == "subject042_night1_s…"
    assert len(name) == 20
