"""Grid lines config row: Vertical grid checkbox (Show_vertical_grid) in the General
section, and the 1 s / axis-tick grid it gates on the EEG panel."""

from config.apply_changes import apply_changes
from config.default_config import default_configuration
from widgets.configurationWindow import GeneralConfiguration


def test_show_vertical_grid_defaults_to_true_in_default_config():
    general_config = default_configuration(1, 100, ["Channel 1"])[0]
    assert general_config["Show_vertical_grid"] is True


def test_vertical_grid_checkbox_reflects_config(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Show_vertical_grid"] = False
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    assert page.checkboxes["Show_vertical_grid"].isChecked() is False

    ui.config[0]["Show_vertical_grid"] = True
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    assert page.checkboxes["Show_vertical_grid"].isChecked() is True


def test_toggling_the_checkbox_writes_it_back_to_the_config(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Show_vertical_grid"] = True
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    page.checkboxes["Show_vertical_grid"].setChecked(False)
    assert ui.config[0]["Show_vertical_grid"] is False
    page.checkboxes["Show_vertical_grid"].setChecked(True)
    assert ui.config[0]["Show_vertical_grid"] is True


def test_turning_the_checkbox_off_removes_the_grid_item_from_the_panel(loaded_ui):
    ui = loaded_ui
    assert ui.SignalWidget.grid_item is not None

    ui.config[0]["Show_vertical_grid"] = False
    apply_changes(["Show_vertical_grid"], ui)
    assert ui.SignalWidget.grid_item is None

    ui.config[0]["Show_vertical_grid"] = True
    apply_changes(["Show_vertical_grid"], ui)
    assert ui.SignalWidget.grid_item is not None


def test_a_config_without_the_key_shows_the_grid(loaded_ui):
    ui = loaded_ui
    del ui.config[0]["Show_vertical_grid"]
    apply_changes([], ui)
    assert ui.SignalWidget.grid_item is not None
