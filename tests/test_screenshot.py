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
    assert filter_.startswith("PNG (*.png);;JPEG (*.jpg)")

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


# --- raster formats ---

def _take_as(ui, monkeypatch, path, filter_, **kw):
    """Like _take, but the user picks `filter_` in the file dialog."""
    choices = Choices(monkeypatch, path=str(path), **kw)
    monkeypatch.setattr(
        dialog_module.QFileDialog, "getSaveFileName",
        lambda parent, caption, start, flt, selected="": (choices.offered.append((start, flt)) or str(path), filter_),
    )
    _whole_window_action(ui).trigger()
    return choices


RASTER = [("PNG", "png", "PNG"), ("JPEG", "jpg", "JPEG"), ("TIFF", "tiff", "TIFF"), ("BMP", "bmp", "BMP"), ("WEBP", "webp", "WEBP")]


@pytest.mark.parametrize("label, ext, fmt", RASTER)
def test_each_raster_format_writes_a_valid_file_of_that_format(loaded_ui, monkeypatch, tmp_path, label, ext, fmt):
    out = tmp_path / f"shot.{ext}"
    _take_as(loaded_ui, monkeypatch, out, f"{label} (*.{ext})", dpi=96)
    assert out.exists()
    from PySide6.QtGui import QImageReader
    reader = QImageReader(str(out))
    assert bytes(reader.format()).decode().upper() == fmt.replace("JPEG", "JPEG")
    window = loaded_ui.centralwidget.window()
    assert reader.size().width() == window.width() and reader.size().height() == window.height()


@pytest.mark.parametrize("label, ext", [("JPEG", "jpg"), ("TIFF", "tiff"), ("BMP", "bmp")])
def test_dpi_metadata_is_written_where_supported(loaded_ui, monkeypatch, tmp_path, label, ext):
    out = tmp_path / f"shot.{ext}"
    _take_as(loaded_ui, monkeypatch, out, f"{label} (*.{ext})", dpi=300)
    assert abs(_dpi(QImage(str(out))) - 300) <= 1


@pytest.mark.parametrize("typed, expected", [
    ("name", "name.jpg"), ("a.png", "a.jpg"), ("a.jpg", "a.jpg"), ("a.JPEG", "a.JPEG"), ("my.rec", "my.rec.jpg"),
])
def test_typed_extension_is_completed_or_replaced_by_the_filter_extension(loaded_ui, monkeypatch, tmp_path, typed, expected):
    out = tmp_path / "out"
    out.mkdir()
    _take_as(loaded_ui, monkeypatch, out / typed, "JPEG (*.jpg)")
    assert [p.name for p in out.iterdir()] == [expected]


@pytest.mark.parametrize("label, ext", [("JPEG", "jpg"), ("TIFF", "tiff"), ("BMP", "bmp"), ("WEBP", "webp"), ("PNG", "png")])
def test_next_suggested_name_uses_the_last_used_format(loaded_ui, monkeypatch, tmp_path, label, ext):
    _take_as(loaded_ui, monkeypatch, tmp_path / "x", f"{label} (*.{ext})")
    choices = _take_as(loaded_ui, monkeypatch, tmp_path / "y", f"{label} (*.{ext})")
    assert choices.offered[0][0].endswith(f".{ext}")
    assert choices.offered[0][1].split(";;")[0] == "PNG (*.png)"
    assert f"{label} (*.{ext})" in choices.offered[0][1]


def test_jpeg_background_is_white_not_black(loaded_ui, monkeypatch, tmp_path):
    out = tmp_path / "shot.jpg"
    _take_as(loaded_ui, monkeypatch, out, "JPEG (*.jpg)", dpi=96)
    image = QImage(str(out))
    colours = [image.pixelColor(x, y) for x in range(0, image.width(), 11) for y in range(0, image.height(), 11)]
    assert any(c.lightness() > 200 for c in colours)
