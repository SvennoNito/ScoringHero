from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel

# Tint per stage; same palette as the sleep report
STAGE_COLORS = {
    "Wake": "#8bbf56",
    "N1": "#aabcce",
    "N2": "#4f9fd8",
    "N3": "#3b3fa8",
    "REM": "#dc5050",
}
UNSCORED_COLOR = "#78808c"
TEXT_COLOR = "#1f2933"
LIGHT_TEXT = "#ffffff"
DISAGREE_BORDER = "#c0392b"
TINT_ALPHA = 170


def stage_tint(stage):
    """Translucent background colour (CSS rgba) for `stage`."""
    c = QColor(STAGE_COLORS.get(stage, UNSCORED_COLOR))
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {TINT_ALPHA})"


def stage_text_color(stage):
    """Text colour readable on the tint of `stage`."""
    return LIGHT_TEXT if stage == "N3" else TEXT_COLOR


class StageBadge(QLabel):
    """Translucent stage chip floating over `panel` (the signal panel). Shows the stage of
    the displayed epoch; 'N2 vs N3' with a red border when the comparison scoring
    disagrees. Drag it with the mouse; `positionChosen(fx, fy)` reports the new centre as
    fractions of the panel size on release."""

    positionChosen = Signal(float, float)

    def __init__(self, panel):
        super().__init__(panel)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.SizeAllCursor)
        self.setToolTip("Drag to move")
        self._position = (0.5, 0.5)
        self._grab = None
        panel.installEventFilter(self)

    def show_stage(self, stage, comparison_stage=None, disagrees=False, position=(0.5, 0.5), size=24):
        text = f'{stage} <span style="color: {DISAGREE_BORDER};">vs {comparison_stage}</span>' if disagrees else stage
        border = DISAGREE_BORDER if disagrees else "transparent"
        self.setStyleSheet(
            f"background: {stage_tint(stage)}; color: {stage_text_color(stage)};"
            f"border: 2px solid {border}; border-radius: {size * 5 // 12}px;"
            f"padding: {size // 8}px {size * 7 // 12}px; font-size: {size}px; font-weight: 700;"
        )
        self.setText(text)
        self.adjustSize()
        self._position = tuple(position)
        self._place()

    def _place(self):
        panel = self.parentWidget()
        fx, fy = self._position
        self._move_to(round(fx * panel.width() - self.width() / 2), round(fy * panel.height() - self.height() / 2))
        self.raise_()

    def _move_to(self, x, y):
        """Move to top-left (x, y), kept inside the panel."""
        panel = self.parentWidget()
        self.move(
            max(0, min(x, panel.width() - self.width())),
            max(0, min(y, panel.height() - self.height())),
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._grab = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self._grab is not None:
            top_left = self.mapToParent(event.position().toPoint() - self._grab)
            self._move_to(top_left.x(), top_left.y())

    def mouseReleaseEvent(self, event):
        if self._grab is None:
            return
        self._grab = None
        panel = self.parentWidget()
        geometry = self.geometry()
        self._position = (
            (geometry.x() + geometry.width() / 2) / panel.width(),
            (geometry.y() + geometry.height() / 2) / panel.height(),
        )
        self.positionChosen.emit(*self._position)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self._place()
        return False
