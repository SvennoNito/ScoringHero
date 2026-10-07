"""The comparison scoring's display name."""

from utilities.epoch_status import comparison_display_name


def test_display_name_drops_folder_and_extension():
    assert comparison_display_name("C:/data/night1/scorer2.txt") == "scorer2"


def test_display_name_keeps_20_character_stem():
    assert comparison_display_name("abcdefghijklmnopqrst.json") == "abcdefghijklmnopqrst"


def test_display_name_cuts_long_stem_with_ellipsis():
    name = comparison_display_name("subject042_night1_scorerB_final.csv")
    assert name == "subject042_night1_s…"
    assert len(name) == 20
