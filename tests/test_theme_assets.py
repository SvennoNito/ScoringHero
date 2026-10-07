"""Bundled font and recolorable icons, observed through the booted headless app."""

from PySide6.QtGui import QColor, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

from style import theme
from style.icons import icon


def test_app_uses_bundled_inter_font(loaded_ui):
    assert "Inter" in QFontDatabase.families()
    assert QApplication.instance().font().family() == "Inter"


def _opaque_colors(pixmap):
    image = pixmap.toImage()
    colors = set()
    for x in range(image.width()):
        for y in range(image.height()):
            pixel = QColor.fromRgba(image.pixel(x, y))
            if pixel.alpha() == 255:
                colors.add(pixel.name())
    return colors


def test_icon_takes_its_colors_from_the_theme_per_state(loaded_ui):
    flag = icon("flag")
    assert _opaque_colors(flag.pixmap(32, 32, QIcon.Normal)) == {theme.ICON}
    assert _opaque_colors(flag.pixmap(32, 32, QIcon.Active)) == {theme.ACCENT}
    assert _opaque_colors(flag.pixmap(32, 32, QIcon.Disabled)) == {theme.DISABLED}
