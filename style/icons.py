from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel

from . import theme

_RENDER_SIZE = 96  # large enough that QIcon scales down crisply at high DPI
_STROKE_WIDTH = "1.5"  # Lucide's default 2 looks heavy at toolbar size


def _pixmap(svg_template, color):
    svg = svg_template.replace('stroke-width="2"', f'stroke-width="{_STROKE_WIDTH}"')
    renderer = QSvgRenderer(QByteArray(svg.replace("currentColor", color).encode()))
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


def info_badge(tooltip, size=16):
    """Accent-colored info icon with a hover tooltip that stays until the mouse leaves."""
    label = QLabel()
    label.setPixmap(icon("info").pixmap(QSize(size, size), QIcon.Active))
    label.setToolTip(tooltip)
    label.setToolTipDuration(0)
    label.setCursor(Qt.WhatsThisCursor)
    return label
