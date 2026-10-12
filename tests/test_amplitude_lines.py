"""Amplitude lines config row: Show_amplitude_lines checkbox in the General section
(Grid lines row), the ± reference / ±3 lines it gates on the EEG panel, the matching
left-axis tick labels, and the live "Amplitude lines (±...)" checkbox label."""

import pyqtgraph as pg
from PySide6.QtWidgets import QCheckBox

from config.apply_changes import apply_changes
from config.default_config import default_configuration
from eeg.displayed_signal import settings_changed
from widgets.configurationWindow import GeneralConfiguration


def _visible_chans(ui):
    return [c for c in ui.config[1] if c["Display_on_screen"]]


def _amplitude_lines(ui):
    return [
        item
        for item in ui.SignalWidget.axes.plotItem.items
        if isinstance(item, pg.InfiniteLine)
        and item.angle == 0
        and item not in ui.SignalWidget.drawn_zerolines
    ]


def test_show_amplitude_lines_defaults_to_true_in_default_config():
    general_config = default_configuration(1, 100, ["Channel 1"])[0]
    assert general_config["Show_amplitude_lines"] is True


def test_amplitude_checkbox_reflects_config(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Show_amplitude_lines"] = False
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    assert page.checkboxes["Show_amplitude_lines"].isChecked() is False

    ui.config[0]["Show_amplitude_lines"] = True
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    assert page.checkboxes["Show_amplitude_lines"].isChecked() is True


def test_toggling_the_checkbox_writes_it_back_to_the_config(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Show_amplitude_lines"] = True
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    page.checkboxes["Show_amplitude_lines"].setChecked(False)
    assert ui.config[0]["Show_amplitude_lines"] is False
    page.checkboxes["Show_amplitude_lines"].setChecked(True)
    assert ui.config[0]["Show_amplitude_lines"] is True


def test_a_config_without_the_key_shows_the_lines(loaded_ui):
    ui = loaded_ui
    del ui.config[0]["Show_amplitude_lines"]
    apply_changes([], ui)
    numchans = len(_visible_chans(ui))
    assert len(_amplitude_lines(ui)) == 2 * numchans


def test_turning_off_removes_amplitude_lines_and_labels_in_muv_mode(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Robust_z_standardize"] = False
    ui.config[0]["Stack_channels"] = False
    numchans = len(_visible_chans(ui))

    ui.config[0]["Show_amplitude_lines"] = True
    apply_changes(["Show_amplitude_lines"], ui)
    assert len(_amplitude_lines(ui)) == 2 * numchans
    left_axis = ui.SignalWidget.axes.getAxis("left")
    assert len(left_axis._tickLevels[0]) == 3

    ui.config[0]["Show_amplitude_lines"] = False
    apply_changes(["Show_amplitude_lines"], ui)
    assert len(_amplitude_lines(ui)) == 0
    left_axis = ui.SignalWidget.axes.getAxis("left")
    assert left_axis._tickLevels[0] == [(left_axis._tickLevels[0][0][0], "0")]


def test_turning_off_removes_amplitude_lines_and_labels_in_z_standardize_mode(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Robust_z_standardize"] = True
    ui.config[0]["Stack_channels"] = False
    numchans = len(_visible_chans(ui))

    ui.config[0]["Show_amplitude_lines"] = False
    settings_changed(ui)
    assert len(_amplitude_lines(ui)) == 0
    left_axis = ui.SignalWidget.axes.getAxis("left")
    assert left_axis._tickLevels[0] == [(left_axis._tickLevels[0][0][0], "0")]

    ui.config[0]["Show_amplitude_lines"] = True
    settings_changed(ui)
    assert len(_amplitude_lines(ui)) == 2 * numchans
    left_axis = ui.SignalWidget.axes.getAxis("left")
    assert len(left_axis._tickLevels[0]) == 3


def test_turning_off_removes_amplitude_lines_in_stacked_mode(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Stack_channels"] = True
    numchans = len(_visible_chans(ui))

    ui.config[0]["Show_amplitude_lines"] = True
    settings_changed(ui)
    assert len(_amplitude_lines(ui)) == 2 * numchans

    ui.config[0]["Show_amplitude_lines"] = False
    settings_changed(ui)
    assert len(_amplitude_lines(ui)) == 0


def test_label_shows_reference_amplitude_in_muv_mode(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Robust_z_standardize"] = False
    ui.config[0]["Reference_amplitude_line_muV"] = 37.5
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    assert page.amplitude_checkbox.text() == "Amplitude lines (\u00b137.5 \u03bcV)"


def test_label_shows_whole_number_amplitude_without_decimal(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Robust_z_standardize"] = False
    ui.config[0]["Reference_amplitude_line_muV"] = 40
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    assert page.amplitude_checkbox.text() == "Amplitude lines (\u00b140 \u03bcV)"


def test_label_shows_plusminus_3_when_z_standardize_checkbox_is_checked(loaded_ui):
    ui = loaded_ui
    z_checkbox = QCheckBox()
    z_checkbox.setChecked(True)
    page = GeneralConfiguration(ui.config[0], allow_staging=False, z_standardize_checkbox=z_checkbox)
    assert page.amplitude_checkbox.text() == "Amplitude lines (\u00b13)"


def test_label_follows_the_reference_amplitude_spinbox_live(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Robust_z_standardize"] = False
    page = GeneralConfiguration(ui.config[0], allow_staging=False)
    page.spinboxes["Reference_amplitude_line_muV"][0].setValue(50)
    assert page.amplitude_checkbox.text() == "Amplitude lines (\u00b150 \u03bcV)"


def test_label_follows_the_z_standardize_checkbox_live(loaded_ui):
    ui = loaded_ui
    z_checkbox = QCheckBox()
    z_checkbox.setChecked(False)
    page = GeneralConfiguration(ui.config[0], allow_staging=False, z_standardize_checkbox=z_checkbox)
    assert "\u03bcV" in page.amplitude_checkbox.text()

    z_checkbox.setChecked(True)
    assert page.amplitude_checkbox.text() == "Amplitude lines (\u00b13)"

    z_checkbox.setChecked(False)
    assert "\u03bcV" in page.amplitude_checkbox.text()
