from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from . import theme

_RENDER_SIZE = 96  # large enough that QIcon scales down crisply at high DPI


def _pixmap(svg_template, color):
    renderer = QSvgRenderer(QByteArray(svg_template.replace("currentColor", color).encode()))
    image = QImage(_RENDER_SIZE, _RENDER_SIZE, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return QPixmap.fromImage(image)


def icon(name):
    """Lucide icon `name` (assets/icons/<name>.svg), recolored from the theme: muted in
    the normal state, accent on hover, grey when disabled."""
    with open(theme.asset_path("icons", f"{name}.svg"), encoding="utf-8") as file:
        svg = file.read()
    result = QIcon()
    result.addPixmap(_pixmap(svg, theme.ICON), QIcon.Normal)
    result.addPixmap(_pixmap(svg, theme.ACCENT), QIcon.Active)
    result.addPixmap(_pixmap(svg, theme.DISABLED), QIcon.Disabled)
    return result
