from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QApplication, QGraphicsItem

from style import theme


class ChannelPill(QGraphicsItem):
    """A channel name in a small rounded, semi-opaque label inside a plot, so it never
    fights with the trace or image behind it. At most `max_fraction` (default a quarter) of the plot widget wide:
    longer names are elided in the middle (suffixes like '-A2' or '*' stay visible) and
    the tooltip then carries the full name.

    The pill ignores view transforms (it is sized in pixels). Place it with setPos in
    data coordinates (vertically centred on that point), or with corner=True as a child
    of a ViewBox, where it sits in the top-left corner. Call refresh() when the plot
    widget is resized."""

    PAD_X, PAD_Y, INSET = 8, 3, 8

    def __init__(self, view, name="", corner=False, max_fraction=0.25):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setZValue(15)
        self._view = view
        self._corner = corner
        self._max_fraction = max_fraction
        self._font = QFont(QApplication.font())
        self._font.setPixelSize(12)
        self._font.setWeight(QFont.DemiBold)
        self._name = name
        self._shown = ""
        self._rect = QRectF()
        self.refresh()

    def text(self):
        """The text as drawn (elided when the name is too wide)."""
        return self._shown

    def set_name(self, name):
        self._name = name
        self.refresh()

    def refresh(self):
        metrics = QFontMetrics(self._font)
        available = int(self._view.viewport().width() * self._max_fraction) - 2 * self.PAD_X
        shown = metrics.elidedText(self._name, Qt.ElideMiddle, max(available, 0))
        width = metrics.horizontalAdvance(shown) + 2 * self.PAD_X
        height = metrics.height() + 2 * self.PAD_Y
        top = self.INSET if self._corner else -height / 2
        rect = QRectF(self.INSET, top, width, height)
        if rect != self._rect:
            self.prepareGeometryChange()
            self._rect = rect
        self._shown = shown
        self.setToolTip(self._name if shown != self._name else "")
        self.setVisible(bool(self._name))

    def boundingRect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(theme.BORDER)))
        painter.setBrush(QColor(*theme.PILL_BACKGROUND))
        radius = self._rect.height() / 2
        painter.drawRoundedRect(self._rect, radius, radius)
        painter.setPen(QColor(theme.TEXT))
        painter.setFont(self._font)
        painter.drawText(self._rect, Qt.AlignCenter, self._shown)
