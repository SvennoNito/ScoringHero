import os

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QDialogButtonBox, QProxyStyle, QStyle

from . import theme

FONT_FILES = ("Inter-Regular.ttf", "Inter-SemiBold.ttf")
FONT_FAMILY = "Inter"


class ThemeStyle(QProxyStyle):
    """Fusion with one button order on every platform: Cancel left of the primary action,
    both flush right (Qt's "Mac" button layout)."""

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.SH_DialogButtonLayout:
            return QDialogButtonBox.ButtonLayout.MacLayout.value
        return super().styleHint(hint, option, widget, returnData)


def register_app_font(app):
    """Make the bundled Inter the application font (same look on every platform; also
    gives the headless offscreen platform real glyphs). Keeps the platform's point size."""
    for name in FONT_FILES:
        QFontDatabase.addApplicationFont(theme.asset_path("fonts", name))
    font = QFont(FONT_FAMILY)
    font.setPointSizeF(app.font().pointSizeF())
    app.setFont(font)


def apply_app_theme(MainWindow, app, app_path, stylesheet):

    app.setStyle(ThemeStyle("Fusion"))
    register_app_font(app)
    with open(os.path.join(app_path, "style", stylesheet), "r") as file:
        stylesheet = file.read()
    app.setStyleSheet(stylesheet)
