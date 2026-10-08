"""Render a widget to a file. No dialogs: callable headless.

`capture(widget, path, format, dpi)` writes one Screenshot. Formats are registered by name
in FORMATS; the file dialog filters are built from the same registry, so a new format is one
entry here."""

from typing import Callable, NamedTuple

from PySide6.QtCore import Qt, QBuffer, QIODevice, QMarginsF, QPoint, QRect, QSize, QSizeF
from PySide6.QtGui import QImage, QPageLayout, QPageSize, QPainter, QPdfWriter, QRegion
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtWidgets import QWidget

from .svg_cosmetic import bake_cosmetic_strokes

SCREEN_DPI = 96  # the unscaled size of a widget corresponds to this many dots per inch
INCH_PER_METER = 0.0254


class Format(NamedTuple):
    label: str  # in the file dialog filter
    extension: str  # without dot
    write: Callable[[QWidget, str, int], None]  # (widget, path, dpi)
    aliases: tuple = ()  # other extensions of the same format, accepted when typed
    vector: bool = False  # DPI is ignored

    def matches(self, extension):
        """Whether `extension` (no dot, lower case) is this format's."""
        return extension in (self.extension, *self.aliases)


class Crop(NamedTuple):
    """An area of a widget as a capture target, so everything lying over a panel (e.g. the
    stage badge) is part of it. Sized like the area; drawn with `draw`."""

    widget: QWidget
    area: QRect

    def width(self):
        return self.area.width()

    def height(self):
        return self.area.height()

    def size(self):
        return self.area.size()


def draw(painter, target):
    """Draw a widget, or a Crop of one, with its top-left at the painter's origin. Writers draw through this."""
    # QWidget.render, not widget.render: QGraphicsView (pyqtgraph) overrides render with another signature
    if isinstance(target, Crop):
        QWidget.render(target.widget, painter, QPoint(0, 0), QRegion(target.area))
    else:
        QWidget.render(target, painter, QPoint(0, 0), QRegion(QRect(QPoint(0, 0), target.size())))


def render_image(widget, dpi, background=0):
    """The widget as it is displayed, drawn at dpi / SCREEN_DPI times its size."""
    scale = dpi / SCREEN_DPI
    size = QSize(round(widget.width() * scale), round(widget.height() * scale))
    image = QImage(size, QImage.Format_ARGB32)
    image.fill(background)  # transparent unless a background is given
    meters = round(dpi / INCH_PER_METER)
    image.setDotsPerMeterX(meters)
    image.setDotsPerMeterY(meters)
    painter = QPainter(image)
    painter.scale(scale, scale)
    draw(painter, widget)
    painter.end()
    return image


def _write_raster(format_name, background=0):
    def write(widget, path, dpi):
        if not render_image(widget, dpi, background).save(path, format_name):
            raise OSError(f"Could not write {path}")

    return write


def _write_svg(widget, path, dpi):
    """Vector; dpi ignored. One user unit per widget pixel; cosmetic pen widths baked into the geometry."""
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    generator = QSvgGenerator()
    generator.setOutputDevice(buffer)
    generator.setSize(widget.size())
    generator.setViewBox(QRect(QPoint(0, 0), widget.size()))
    generator.setResolution(SCREEN_DPI)
    painter = QPainter(generator)
    draw(painter, widget)
    painter.end()
    svg = bake_cosmetic_strokes(bytes(buffer.data()).decode("utf-8"))
    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write(svg)


def _write_pdf(widget, path, dpi):
    """Vector; dpi ignored. One page as large as the widget (one device pixel is 1/96 inch)."""
    writer = QPdfWriter(path)
    writer.setResolution(SCREEN_DPI)
    writer.setPageSize(QPageSize(QSizeF(widget.width(), widget.height()) / SCREEN_DPI, QPageSize.Inch))
    writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Inch)
    painter = QPainter(writer)
    draw(painter, widget)
    painter.end()


FORMATS = {
    "png": Format("PNG", "png", _write_raster("PNG")),
    "jpeg": Format("JPEG", "jpg", _write_raster("JPEG", background=Qt.white), aliases=("jpeg",)),  # no alpha: on white
    "tiff": Format("TIFF", "tiff", _write_raster("TIFF"), aliases=("tif",)),
    "bmp": Format("BMP", "bmp", _write_raster("BMP")),
    "webp": Format("WEBP", "webp", _write_raster("WEBP")),
    "svg": Format("SVG", "svg", _write_svg, vector=True),
    "pdf": Format("PDF", "pdf", _write_pdf, vector=True),
}


def capture(widget, path, format, dpi):
    """Write `widget` to `path` as `format` (a key of FORMATS) at `dpi`."""
    FORMATS[format].write(widget, path, dpi)
