"""Utilities > Screenshot: the options dialog and the file dialog around `capture`.

`take_screenshot(ui, name, target, ...)` is the whole flow for one Screenshot; each menu
action only says what to capture: `name` goes into the suggested file name and `target`
is the widget."""

import os

from PySide6.QtCore import QPoint, QRect
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QLabel, QMessageBox, QSpinBox, QVBoxLayout,
)

from .capture import FORMATS, Crop, capture

DPI_MIN, DPI_MAX, DPI_DEFAULT = 72, 1200, 200


class ScreenshotOptionsDialog(QDialog):
    """DPI and, for the whole window, whether the menu bar and status bar are included."""

    def __init__(self, parent, include_bars_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Screenshot")

        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(DPI_MIN, DPI_MAX)
        self.spin_dpi.setValue(DPI_DEFAULT)
        self.spin_dpi.setSuffix(" dpi")

        self.cb_bars = QCheckBox("Include menu bar and status bar")
        self.cb_bars.setChecked(True)
        self.cb_bars.setEnabled(include_bars_enabled)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout()
        form.addRow("Resolution:", self.spin_dpi)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.cb_bars)
        layout.addWidget(QLabel("Resolution is ignored for SVG and PDF (vector formats)."))
        layout.addWidget(buttons)

    def dpi(self):
        return self.spin_dpi.value()

    def include_bars(self):
        return self.cb_bars.isChecked()


def _filter(name):
    return f"{FORMATS[name].label} (*.{FORMATS[name].extension})"


def _format_chosen(path, selected_filter, fallback):
    """Name of the format the user picked: by filter, else by typed extension, else `fallback`."""
    for name in FORMATS:
        if selected_filter == _filter(name):
            return name
    extension = os.path.splitext(path)[1][1:].lower()
    return next((name for name, f in FORMATS.items() if f.matches(extension)), fallback)


def _with_extension(path, format):
    """`path` ending in the format's extension: kept if it has one, a known image extension is replaced, else appended."""
    stem, typed = os.path.splitext(path)
    f = FORMATS[format]
    typed = typed[1:].lower()
    if f.matches(typed):
        return path
    if any(g.matches(typed) for g in FORMATS.values()):
        return f"{stem}.{f.extension}"
    return f"{path}.{f.extension}"


def suggested_name(ui, name, format):
    """`<recording>_<name>_epochXYZ.<ext>`; XYZ is the displayed epoch number."""
    recording = os.path.basename(ui.filename)
    return f"{recording}_{name}_epoch{ui.this_epoch + 1:03d}.{FORMATS[format].extension}"


def take_screenshot(ui, name, target, with_bars_option=False):
    """Ask for the options, then for the file, then write the Screenshot.

    `target(include_bars)` returns the widget to capture; `with_bars_option` enables the
    "Include menu bar and status bar" checkbox (whole window only). Cancel at either
    dialog writes nothing."""
    parent = ui.centralwidget.window()
    options = ScreenshotOptionsDialog(parent, include_bars_enabled=with_bars_option)
    if not options.exec():
        return
    widget = target(options.include_bars() if with_bars_option else True)

    start = os.path.join(ui.screenshot_path or ui.default_data_path, suggested_name(ui, name, ui.screenshot_format))
    path, selected_filter = QFileDialog.getSaveFileName(
        parent, "Save screenshot", start, ";;".join(_filter(n) for n in FORMATS), _filter(ui.screenshot_format)
    )
    if not path:
        return
    format = _format_chosen(path, selected_filter, ui.screenshot_format)
    path = _with_extension(path, format)

    try:
        capture(widget, path, format, options.dpi())
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"An error occurred while writing the screenshot\n{path}:\n\n{e}")
        return
    ui.screenshot_format = format
    ui.screenshot_path = os.path.dirname(path)


def screenshot_window(ui):
    """Utilities > Screenshot > Whole window: the main window, or its central area only."""
    take_screenshot(
        ui, "window",
        lambda include_bars: ui.centralwidget.window() if include_bars else ui.centralwidget,
        with_bars_option=True,
    )


# Panel name (menu text and file name) -> the widget showing it
PANELS = {
    "Signal": lambda ui: ui.SignalWidget.axes,
    "Spectrogram": lambda ui: ui.SpectogramWidget.graphics,
    "Hypnogram": lambda ui: ui.HypnogramWidget.axes,
    "Rectangle power": lambda ui: ui.RectanglePower.axes,
    "Time-frequency": lambda ui: ui.TFWidget.graphics,
}


def panel_visible(ui, name):
    return PANELS[name](ui).isVisibleTo(ui.centralwidget)


def update_panel_actions(ui):
    """Enable each Panel entry only while its panel is visible."""
    for name, action in ui.action_screenshot_panels.items():
        action.setEnabled(panel_visible(ui, name))


def screenshot_panel(ui, name):
    """Utilities > Screenshot > Panel > <name>: that panel only, with what lies over it."""
    panel = PANELS[name](ui)
    area = QRect(panel.mapTo(ui.centralwidget, QPoint(0, 0)), panel.size())
    take_screenshot(ui, name.lower().replace(" ", "_"), lambda _: Crop(ui.centralwidget, area))
