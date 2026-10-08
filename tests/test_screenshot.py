"""Utilities > Screenshot, observed through the menu actions of the booted app. The options
dialog and the native file dialog are replaced by fixed choices; the files written are read back."""

import os

import pytest
from PySide6.QtGui import QImage

import screenshot.screenshot_dialog as dialog_module

DPI_TOLERANCE = 1  # dots per meter round to an integer, so DPI read back is off by a fraction


def _utilities(ui):
    return {a.text(): a.menu() for a in ui.menu.actions()}["Utilities"]


def _screenshot_menu(ui):
    return {a.text(): a.menu() for a in _utilities(ui).actions() if a.menu()}["Screenshot"]


def _whole_window_action(ui):
    return {a.text(): a for a in _screenshot_menu(ui).actions()}["Whole window…"]


class Choices:
    """Fixed answers for the options dialog and the file dialog; records what was offered."""

    def __init__(self, monkeypatch, path=None, dpi=200, include_bars=True, cancel_options=False):
        self.path, self.dpi, self.include_bars = path, dpi, include_bars
        self.offered = []  # (start path, filter) per file dialog
        self.errors = []
        choices = self

        class Options:
            def __init__(self, parent, include_bars_enabled=True):
                pass

            def exec(self):
                return not cancel_options

            def dpi(self):
                return choices.dpi

            def include_bars(self):
                return choices.include_bars

        def get_save_file_name(parent, caption, start, filter_, selected=""):
            choices.offered.append((start, filter_))
            return (choices.path or "", selected)

        monkeypatch.setattr(dialog_module, "ScreenshotOptionsDialog", Options)
        monkeypatch.setattr(dialog_module.QFileDialog, "getSaveFileName", get_save_file_name)
        monkeypatch.setattr(dialog_module.QMessageBox, "critical", lambda parent, title, text: choices.errors.append(text))


def _take(ui, monkeypatch, path, **kw):
    choices = Choices(monkeypatch, path=str(path), **kw)
    _whole_window_action(ui).trigger()
    return choices


def _dpi(image):
    return round(image.dotsPerMeterX() * 0.0254)


def test_screenshot_entries_wait_for_a_recording(unloaded_ui, loaded_ui):
    assert not _utilities(unloaded_ui).isEnabled()
    assert _utilities(loaded_ui).isEnabled()
    assert _screenshot_menu(loaded_ui).isEnabled()


@pytest.mark.parametrize("dpi", [72, 200, 600])
def test_png_is_scaled_by_dpi_and_carries_the_dpi(loaded_ui, monkeypatch, tmp_path, dpi):
    ui = loaded_ui
    window = ui.centralwidget.window()
    _take(ui, monkeypatch, tmp_path / "shot.png", dpi=dpi)

    image = QImage(str(tmp_path / "shot.png"))
    assert not image.isNull()
    assert image.width() == round(window.width() * dpi / 96)
    assert image.height() == round(window.height() * dpi / 96)
    assert abs(_dpi(image) - dpi) <= DPI_TOLERANCE


def test_without_menu_bar_and_status_bar_the_image_is_smaller(loaded_ui, monkeypatch, tmp_path):
    _take(loaded_ui, monkeypatch, tmp_path / "with.png", include_bars=True)
    _take(loaded_ui, monkeypatch, tmp_path / "without.png", include_bars=False)

    with_bars, without = QImage(str(tmp_path / "with.png")), QImage(str(tmp_path / "without.png"))
    assert without.width() * without.height() < with_bars.width() * with_bars.height()


def test_image_shows_the_window_not_blank(loaded_ui, monkeypatch, tmp_path):
    _take(loaded_ui, monkeypatch, tmp_path / "shot.png")
    image = QImage(str(tmp_path / "shot.png"))
    colours = {image.pixel(x, y) for x in range(0, image.width(), 37) for y in range(0, image.height(), 37)}
    assert len(colours) > 5


def test_suggested_name_is_recording_window_and_padded_epoch(loaded_ui, monkeypatch, tmp_path):
    ui = loaded_ui
    ui.this_epoch = 6  # displayed as epoch 7
    choices = _take(ui, monkeypatch, tmp_path / "x.png")
    start, filter_ = choices.offered[0]
    assert os.path.basename(start) == "example_data_window_epoch007.png"
    assert filter_ == "PNG (*.png)"

    ui.this_epoch = 233
    choices = _take(ui, monkeypatch, tmp_path / "x.png")
    assert os.path.basename(choices.offered[0][0]) == "example_data_window_epoch234.png"


def test_start_folder_is_data_folder_then_last_screenshot_folder(loaded_ui, monkeypatch, tmp_path):
    ui = loaded_ui
    data_folder = ui.default_data_path
    target = tmp_path / "figures"
    target.mkdir()

    choices = _take(ui, monkeypatch, tmp_path / "first" / "a.png")  # folder missing: write fails
    assert os.path.dirname(choices.offered[0][0]) == data_folder

    choices = _take(ui, monkeypatch, target / "a.png")
    assert os.path.dirname(choices.offered[0][0]) == data_folder
    assert (target / "a.png").exists()

    choices = _take(ui, monkeypatch, target / "b.png")
    assert os.path.dirname(choices.offered[0][0]) == str(target)
    assert ui.default_data_path == data_folder  # scoring I/O is unaffected


def test_loading_another_recording_before_the_first_screenshot_moves_the_default(loaded_ui, monkeypatch, tmp_path):
    ui = loaded_ui
    other = tmp_path / "other"
    other.mkdir()
    ui.default_data_path = str(other)  # what opening a recording from there does
    choices = _take(ui, monkeypatch, tmp_path / "a.png")
    assert os.path.dirname(choices.offered[0][0]) == str(other)


def test_cancel_at_either_dialog_writes_nothing(loaded_ui, monkeypatch, tmp_path):
    ui = loaded_ui
    _take(ui, monkeypatch, tmp_path / "a.png", cancel_options=True)
    _take(ui, monkeypatch, "")  # file dialog cancelled
    assert list(tmp_path.glob("*.png")) == []
    assert ui.screenshot_path is None


def test_failed_write_shows_an_error_and_leaves_state_unchanged(loaded_ui, monkeypatch, tmp_path):
    ui = loaded_ui
    choices = _take(ui, monkeypatch, tmp_path / "missing_folder" / "a.png")
    assert len(choices.errors) == 1
    assert "missing_folder" in choices.errors[0]
    assert ui.screenshot_path is None


def test_extension_follows_the_filter(loaded_ui, monkeypatch, tmp_path):
    _take(loaded_ui, monkeypatch, tmp_path / "typed_name")
    assert (tmp_path / "typed_name.png").exists()
    assert not (tmp_path / "typed_name").exists()


def test_options_dialog_defaults_and_limits(loaded_ui, monkeypatch, tmp_path):
    seen = {}

    def exec_(self):
        seen.update(dpi=self.dpi(), include_bars=self.include_bars(),
                    low=self.spin_dpi.minimum(), high=self.spin_dpi.maximum())
        return False

    monkeypatch.setattr(dialog_module.ScreenshotOptionsDialog, "exec", exec_)
    _whole_window_action(loaded_ui).trigger()
    assert seen == {"dpi": 200, "include_bars": True, "low": 72, "high": 1200}


# ---- Panel screenshots ---------------------------------------------------------------------

PANEL_ITEMS = ["Signal…", "Spectrogram…", "Hypnogram…", "Rectangle power…", "Time-frequency…"]


def _panel_menu(ui):
    return {a.text(): a.menu() for a in _screenshot_menu(ui).actions() if a.menu()}["Panel"]


def _panel_action(ui, name):
    return {a.text(): a for a in _panel_menu(ui).actions()}[name + "…"]


def _take_panel(ui, monkeypatch, name, path, **kw):
    choices = Choices(monkeypatch, path=str(path), **kw)
    _panel_action(ui, name).trigger()
    return choices


def _show_tf_panel(ui, visible):
    from utilities.apply_tf_visibility import apply_tf_visibility

    ui.config[0]["Wavelet_panel_visible"] = visible
    apply_tf_visibility(ui)


def _lay_out(ui):
    """Show the window at a fixed size so the panels sit at their real places."""
    from PySide6.QtWidgets import QApplication

    window = ui.centralwidget.window()
    window.resize(1400, 900)
    window.show()
    QApplication.processEvents()
    return window


def test_panel_menu_lists_the_five_panels(loaded_ui):
    assert [a.text() for a in _panel_menu(loaded_ui).actions()] == PANEL_ITEMS
    assert _panel_menu(loaded_ui).isEnabled()


def test_panel_entries_wait_for_a_recording(unloaded_ui):
    assert not _utilities(unloaded_ui).isEnabled()


def test_hidden_panel_entry_is_disabled(loaded_ui):
    ui = loaded_ui
    _show_tf_panel(ui, False)
    assert not _panel_action(ui, "Time-frequency").isEnabled()
    assert _panel_action(ui, "Signal").isEnabled()
    _show_tf_panel(ui, True)
    assert _panel_action(ui, "Time-frequency").isEnabled()


@pytest.mark.parametrize("name", ["Signal", "Spectrogram", "Hypnogram", "Rectangle power", "Time-frequency"])
def test_panel_png_is_smaller_than_the_window_and_not_blank(loaded_ui, monkeypatch, tmp_path, name):
    _take(loaded_ui, monkeypatch, tmp_path / "window.png")
    _take_panel(loaded_ui, monkeypatch, name, tmp_path / "panel.png")

    window, panel = QImage(str(tmp_path / "window.png")), QImage(str(tmp_path / "panel.png"))
    assert not panel.isNull()
    assert panel.width() * panel.height() < window.width() * window.height()
    assert abs(_dpi(panel) - 200) <= DPI_TOLERANCE
    colours = {panel.pixel(x, y) for x in range(0, panel.width(), 7) for y in range(0, panel.height(), 7)}
    assert len(colours) > 3


def test_panel_capture_is_that_area_of_the_window_capture(loaded_ui, monkeypatch, tmp_path):
    ui = loaded_ui
    _lay_out(ui)
    _take(ui, monkeypatch, tmp_path / "window.png", include_bars=False)
    _take_panel(ui, monkeypatch, "Hypnogram", tmp_path / "panel.png")

    window, panel = QImage(str(tmp_path / "window.png")), QImage(str(tmp_path / "panel.png"))
    origin = ui.HypnogramWidget.axes.mapTo(ui.centralwidget, ui.HypnogramWidget.axes.rect().topLeft())
    scale = 200 / 96
    area = window.copy(round(origin.x() * scale), round(origin.y() * scale), panel.width(), panel.height())
    points = [(x, y) for x in range(0, panel.width(), 3) for y in range(0, panel.height(), 3)]
    differing = sum(area.pixel(x, y) != panel.pixel(x, y) for x, y in points)
    assert differing < 0.1 * len(points)  # antialiasing at fractional scale differs a little


def test_signal_panel_includes_the_stage_badge(loaded_ui, monkeypatch, tmp_path):
    ui = loaded_ui
    _lay_out(ui)
    badge = ui.StatusReadout.stage_badge
    ui.config[0]["Show_stage_badge"] = True
    badge.show()
    _take_panel(ui, monkeypatch, "Signal", tmp_path / "with.png")
    badge.hide()
    _take_panel(ui, monkeypatch, "Signal", tmp_path / "without.png")
    assert QImage(str(tmp_path / "with.png")) != QImage(str(tmp_path / "without.png"))


def test_panel_options_dialog_disables_the_bars_checkbox(loaded_ui, monkeypatch):
    seen = {}

    monkeypatch.setattr(dialog_module.ScreenshotOptionsDialog, "exec", lambda self: False)
    real_init = dialog_module.ScreenshotOptionsDialog.__init__

    def spy(self, parent, include_bars_enabled=True):
        seen["enabled"] = include_bars_enabled
        real_init(self, parent, include_bars_enabled)

    monkeypatch.setattr(dialog_module.ScreenshotOptionsDialog, "__init__", spy)
    _panel_action(loaded_ui, "Signal").trigger()
    assert seen == {"enabled": False}
    options = dialog_module.ScreenshotOptionsDialog(None, include_bars_enabled=False)
    assert not options.cb_bars.isEnabled()


def test_panel_suggested_name_has_panel_and_padded_epoch(loaded_ui, monkeypatch, tmp_path):
    ui = loaded_ui
    ui.this_epoch = 6
    choices = _take_panel(ui, monkeypatch, "Rectangle power", tmp_path / "x.png")
    assert os.path.basename(choices.offered[0][0]) == "example_data_rectangle_power_epoch007.png"
    choices = _take_panel(ui, monkeypatch, "Time-frequency", tmp_path / "x.png")
    assert os.path.basename(choices.offered[0][0]) == "example_data_time-frequency_epoch007.png"


def test_panel_folder_behaviour_matches_the_window_screenshot(loaded_ui, monkeypatch, tmp_path):
    ui = loaded_ui
    data_folder = ui.default_data_path
    target = tmp_path / "figures"
    target.mkdir()

    choices = _take_panel(ui, monkeypatch, "Signal", target / "a.png")
    assert os.path.dirname(choices.offered[0][0]) == data_folder
    choices = _take(ui, monkeypatch, target / "b.png")  # window shares the folder with panels
    assert os.path.dirname(choices.offered[0][0]) == str(target)
    assert ui.default_data_path == data_folder


def test_panel_cancel_and_failed_write(loaded_ui, monkeypatch, tmp_path):
    ui = loaded_ui
    _take_panel(ui, monkeypatch, "Signal", tmp_path / "a.png", cancel_options=True)
    _take_panel(ui, monkeypatch, "Signal", "")
    assert list(tmp_path.glob("*.png")) == []
    choices = _take_panel(ui, monkeypatch, "Signal", tmp_path / "missing" / "a.png")
    assert len(choices.errors) == 1
    assert ui.screenshot_path is None
