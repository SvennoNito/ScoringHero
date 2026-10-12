"""Zero lines toggle: Show_zero_lines checkbox in the Grid lines row (General
section), gating per-channel zero lines on the EEG panel in every mode."""

from config.apply_changes import apply_changes
from config.default_config import default_configuration
from widgets.configurationWindow import GeneralConfiguration


def test_show_zero_lines_defaults_to_true_in_default_config():
    general_config = default_configuration(1, 100, ["Channel 1"])[0]
    assert general_config["Show_zero_lines"] is True


def test_zero_lines_checkbox_reflects_config(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Show_zero_lines"] = False
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    assert page.checkboxes["Show_zero_lines"].isChecked() is False

    ui.config[0]["Show_zero_lines"] = True
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    assert page.checkboxes["Show_zero_lines"].isChecked() is True


def test_toggling_the_checkbox_writes_it_back_to_the_config(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Show_zero_lines"] = True
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    page.checkboxes["Show_zero_lines"].setChecked(False)
    assert ui.config[0]["Show_zero_lines"] is False
    page.checkboxes["Show_zero_lines"].setChecked(True)
    assert ui.config[0]["Show_zero_lines"] is True


def test_turning_the_checkbox_off_removes_zero_lines_in_muv_mode(loaded_ui):
    ui = loaded_ui
    assert len(ui.SignalWidget.drawn_zerolines) > 0

    ui.config[0]["Show_zero_lines"] = False
    apply_changes(["Show_zero_lines"], ui)
    assert ui.SignalWidget.drawn_zerolines == []

    ui.config[0]["Show_zero_lines"] = True
    apply_changes(["Show_zero_lines"], ui)
    assert len(ui.SignalWidget.drawn_zerolines) > 0


def test_turning_the_checkbox_off_removes_zero_lines_in_z_standardize_mode(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Robust_z_standardize"] = True
    ui.config[0]["Show_zero_lines"] = False
    apply_changes(["Robust_z_standardize", "Show_zero_lines"], ui)
    assert ui.SignalWidget.drawn_zerolines == []

    ui.config[0]["Show_zero_lines"] = True
    apply_changes(["Show_zero_lines"], ui)
    assert len(ui.SignalWidget.drawn_zerolines) > 0


def test_turning_the_checkbox_off_removes_zero_lines_in_stacked_mode(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Stack_channels"] = True
    ui.config[0]["Show_zero_lines"] = False
    apply_changes(["Stack_channels", "Show_zero_lines"], ui)
    assert ui.SignalWidget.drawn_zerolines == []

    ui.config[0]["Show_zero_lines"] = True
    apply_changes(["Show_zero_lines"], ui)
    assert len(ui.SignalWidget.drawn_zerolines) > 0


def test_a_config_without_the_key_shows_the_zero_lines(loaded_ui):
    ui = loaded_ui
    del ui.config[0]["Show_zero_lines"]
    apply_changes([], ui)
    assert len(ui.SignalWidget.drawn_zerolines) > 0


def test_vertical_grid_and_amplitude_lines_unaffected_by_zero_lines_toggle(loaded_ui):
    import pyqtgraph as pg

    ui = loaded_ui
    ui.config[0]["Show_zero_lines"] = False
    apply_changes(["Show_zero_lines"], ui)

    assert ui.SignalWidget.grid_item is not None
    other_horizontal_lines = [
        item
        for item in ui.SignalWidget.axes.plotItem.items
        if isinstance(item, pg.InfiniteLine) and item.angle == 0
    ]
    numchans = len([c for c in ui.config[1] if c["Display_on_screen"]])
    assert len(other_horizontal_lines) == 2 * numchans
