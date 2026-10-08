"""Render a widget to a file. No dialogs: callable headless.

`capture(widget, path, format, dpi)` writes one Screenshot. Formats are registered by name
in FORMATS; the file dialog filters are built from the same registry, so a new format is one
entry here."""

from typing import Callable, NamedTuple

from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtGui import QImage, QPainter, QRegion
from PySide6.QtWidgets import QWidget

SCREEN_DPI = 96  # the unscaled size of a widget corresponds to this many dots per inch
INCH_PER_METER = 0.0254


class Format(NamedTuple):
    label: str  # in the file dialog filter
    extension: str  # without dot
    write: Callable[[QWidget, str, int], None]  # (widget, path, dpi)


def render_image(widget, dpi):
    """The widget as it is displayed, drawn at dpi / SCREEN_DPI times its size."""
    scale = dpi / SCREEN_DPI
    size = QSize(round(widget.width() * scale), round(widget.height() * scale))
    image = QImage(size, QImage.Format_ARGB32)
    image.fill(0)  # transparent
    meters = round(dpi / INCH_PER_METER)
    image.setDotsPerMeterX(meters)
    image.setDotsPerMeterY(meters)
    painter = QPainter(image)
    painter.scale(scale, scale)
    # QWidget.render, not widget.render: QGraphicsView (pyqtgraph) overrides render with another signature
    QWidget.render(widget, painter, QPoint(0, 0), QRegion(QRect(QPoint(0, 0), widget.size())))
    painter.end()
    return image


def _write_raster(format_name):
    def write(widget, path, dpi):
        if not render_image(widget, dpi).save(path, format_name):
            raise OSError(f"Could not write {path}")

    return write


FORMATS = {
    "png": Format("PNG", "png", _write_raster("PNG")),
}


def capture(widget, path, format, dpi):
    """Write `widget` to `path` as `format` (a key of FORMATS) at `dpi`."""
    FORMATS[format].write(widget, path, dpi)
