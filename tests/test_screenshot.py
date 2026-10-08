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


# --- vector formats ---

VECTOR = [("SVG", "svg"), ("PDF", "pdf")]


def _panel_of(name):
    return {"Signal": 0, "Spectrogram": 1, "Hypnogram": 2, "Rectangle power": 3, "Time-frequency": 4}[name]


def _take_panel_as(ui, monkeypatch, name, path, filter_, **kw):
    choices = Choices(monkeypatch, path=str(path), **kw)
    monkeypatch.setattr(
        dialog_module.QFileDialog, "getSaveFileName",
        lambda parent, caption, start, flt, selected="": (choices.offered.append((start, flt)) or str(path), filter_),
    )
    _panel_action(ui, name).trigger()
    return choices


def _svg_size(text):
    """Size in widget pixels: the viewBox (width/height attributes are in mm)."""
    import re

    return tuple(float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', text).groups())


def test_file_dialog_offers_svg_and_pdf(loaded_ui, monkeypatch, tmp_path):
    choices = _take(loaded_ui, monkeypatch, tmp_path / "x.png")
    assert "SVG (*.svg)" in choices.offered[0][1] and "PDF (*.pdf)" in choices.offered[0][1]


def test_whole_window_svg_has_text_and_paths_not_one_raster(loaded_ui, monkeypatch, tmp_path):
    out = tmp_path / "w.svg"
    _take_as(loaded_ui, monkeypatch, out, "SVG (*.svg)")
    text = out.read_text(encoding="utf-8")
    assert text.lstrip().startswith("<?xml") and "<svg" in text and text.rstrip().endswith("</svg>")
    assert "<text" in text
    assert text.count("<path") > 10
    assert text.count("<image") < text.count("<path")


def test_svg_ignores_dpi(loaded_ui, monkeypatch, tmp_path):
    _lay_out(loaded_ui)  # the first capture of a window not yet shown would lay it out differently from the next
    _take_as(loaded_ui, monkeypatch, tmp_path / "a.svg", "SVG (*.svg)", dpi=72)
    _take_as(loaded_ui, monkeypatch, tmp_path / "b.svg", "SVG (*.svg)", dpi=1200)
    assert (tmp_path / "a.svg").read_bytes() == (tmp_path / "b.svg").read_bytes()


def test_svg_is_sized_like_the_window(loaded_ui, monkeypatch, tmp_path):
    out = tmp_path / "w.svg"
    _take_as(loaded_ui, monkeypatch, out, "SVG (*.svg)")
    window = loaded_ui.centralwidget.window()
    assert _svg_size(out.read_text(encoding="utf-8")) == (window.width(), window.height())


def test_whole_window_pdf_is_valid_and_ignores_dpi(loaded_ui, monkeypatch, tmp_path):
    _take_as(loaded_ui, monkeypatch, tmp_path / "a.pdf", "PDF (*.pdf)", dpi=72)
    _take_as(loaded_ui, monkeypatch, tmp_path / "b.pdf", "PDF (*.pdf)", dpi=1200)
    a = (tmp_path / "a.pdf").read_bytes()
    assert a.startswith(b"%PDF-") and b"%%EOF" in a[-32:]
    assert b"/Count 1" in a  # a single page
    # creation date differs between runs; the page size is what DPI could change
    import re

    assert re.search(rb"/MediaBox \[[^\]]*\]", a).group() == re.search(rb"/MediaBox \[[^\]]*\]", (tmp_path / "b.pdf").read_bytes()).group()


def test_without_bars_the_svg_is_smaller(loaded_ui, monkeypatch, tmp_path):
    _take_as(loaded_ui, monkeypatch, tmp_path / "full.svg", "SVG (*.svg)")
    _take_as(loaded_ui, monkeypatch, tmp_path / "plots.svg", "SVG (*.svg)", include_bars=False)
    full = _svg_size((tmp_path / "full.svg").read_text(encoding="utf-8"))
    plots = _svg_size((tmp_path / "plots.svg").read_text(encoding="utf-8"))
    assert plots[1] < full[1]


@pytest.mark.parametrize("name", ["Signal", "Spectrogram", "Hypnogram", "Rectangle power", "Time-frequency"])
@pytest.mark.parametrize("label, ext", VECTOR)
def test_each_visible_panel_writes_a_valid_vector_file(loaded_ui, monkeypatch, tmp_path, name, label, ext):
    ui = loaded_ui
    _show_tf_panel(ui, True)
    _lay_out(ui)
    action = _panel_action(ui, name)
    if not action.isEnabled():
        pytest.skip("panel not visible in this setup")
    out = tmp_path / f"p.{ext}"
    _take_panel_as(ui, monkeypatch, name, out, f"{label} (*.{ext})")
    data = out.read_bytes()
    if ext == "svg":
        assert b"<svg" in data and data.rstrip().endswith(b"</svg>")
        w, h = _svg_size(data.decode("utf-8"))
        window = ui.centralwidget.window()
        assert w < window.width() or h < window.height()
    else:
        assert data.startswith(b"%PDF-") and b"%%EOF" in data[-32:]


def test_panel_svg_is_vector_for_curves(loaded_ui, monkeypatch, tmp_path):
    _lay_out(loaded_ui)
    out = tmp_path / "s.svg"
    _take_panel_as(loaded_ui, monkeypatch, "Signal", out, "SVG (*.svg)")
    assert out.read_text(encoding="utf-8").count("<path") > 1


def test_options_dialog_says_dpi_is_ignored_for_vector(loaded_ui):
    from PySide6.QtWidgets import QLabel

    dialog = dialog_module.ScreenshotOptionsDialog(loaded_ui.centralwidget.window())
    notes = " ".join(l.text() for l in dialog.findChildren(QLabel))
    assert "SVG" in notes and "PDF" in notes and "ignored" in notes


def test_svg_strokes_do_not_depend_on_non_scaling_stroke_support(loaded_ui, monkeypatch, tmp_path):
    """Viewers that ignore vector-effect (Inkscape, Illustrator) scale a stroke with its group's transform:
    no group may both scale and hold cosmetic-pen lines."""
    import re

    _lay_out(loaded_ui)
    out = tmp_path / "w.svg"
    _take_as(loaded_ui, monkeypatch, out, "SVG (*.svg)")
    text = out.read_text(encoding="utf-8")
    for transform, body in re.findall(r'<g [^>]*transform="matrix\(([^)]*)\)"[^>]*>(.*?)</g>', text, re.S):
        if transform.split(",")[:4] != ["1", "0", "0", "1"]:
            assert 'vector-effect="non-scaling-stroke"' not in body
    assert text.count("<polyline") < 2000  # curves are joined, not one element per segment


def test_svg_curve_stays_where_the_widget_draws_it(loaded_ui, monkeypatch, tmp_path):
    """The first channel's curve in the SVG spans the signal panel horizontally, in pixel coordinates."""
    import re

    _lay_out(loaded_ui)
    out = tmp_path / "s.svg"
    _take_panel_as(loaded_ui, monkeypatch, "Signal", out, "SVG (*.svg)")
    text = out.read_text(encoding="utf-8")
    width, height = _svg_size(text)
    xs = [float(x) for points in re.findall(r'<polyline[^>]*points="([^"]*)"', text) for x, _ in (p.split(",") for p in points.split())]
    assert xs and min(xs) >= -1 and max(xs) <= width + 1
    assert max(xs) - min(xs) > 0.5 * width
