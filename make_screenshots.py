"""Build the README screenshots (screenshots/<name>.png and .svg) from example_data.

    uv run python make_screenshots.py              # all
    uv run python make_screenshots.py main filter  # only these
    uv run python make_screenshots.py --list       # names

Every screenshot boots the app offscreen on a temp copy of example_data (tracked files
are never touched), sets up its state (epoch 100, seeded example events, settings) and
renders the panel/window once to a QImage (png) and once to a QSvgGenerator (svg).
Raster-only content (report page, heatmap panels) is embedded as an image in the svg.
"""

import argparse
import os
import random
import shutil
import sys
import tempfile
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import json  # noqa: E402

from PySide6.QtCore import QPoint, QRect, QSize  # noqa: E402
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QRegion  # noqa: E402
from PySide6.QtPdf import QPdfDocument  # noqa: E402
from PySide6.QtSvg import QSvgGenerator  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox, QScrollArea, QWidget  # noqa: E402

from tests.conftest import EXAMPLE_DIR, _boot, _copy_example  # noqa: E402

OUT_DIR = os.path.join(ROOT, "screenshots")
EPOCH = 100  # 1-based, as displayed
COMPARISON_FILE = os.path.join(EXAMPLE_DIR, "example_data2.json")
EVENT_LABELS = {0: "Artifact", 1: "Spindle", 2: "K-complex", 3: "Slow wave", 4: "Arousal"}


# ---- state -------------------------------------------------------------------------


def seed_events(ui, seed=1):
    """Example events over the whole night, none within 40 s of epoch EPOCH. Counts and
    total durations as in the Events tab screenshot (the existing artefact included)."""
    rng = random.Random(seed)
    n_epochs, length = ui.numepo, ui.config[0]["Epoch_length_s"]
    stages = ui.scoring.stages()
    taken = {EPOCH - 2, EPOCH - 1, EPOCH, 243}  # epoch 244 holds the artefact of the example

    def free(candidates, n):
        pool = [e for e in candidates if e not in taken]
        picked = rng.sample(pool, n)
        taken.update(picked)
        return picked

    def spans(slot_epochs, durations):
        return [(e * length + (t := round(rng.uniform(0, length - d), 1)), e * length + t + d)
                for e, d in zip(slot_epochs, durations)]

    def durations(n, lo, hi, total):
        raw = [rng.uniform(lo, hi) for _ in range(n)]
        d = [round(x * total / sum(raw), 1) for x in raw]  # scaled to the total, 0.1 s resolution
        d[d.index(max(d))] = round(max(d) + total - sum(d), 1)
        return d

    deep = [i for i, s in enumerate(stages) if s in ("N2", "N3")]
    anywhere = range(n_epochs)
    plan = {
        0: (anywhere, [22.5, 25.0, 20.0, 25.0]),
        1: (deep, durations(40, 0.5, 2.0, 47.8)),
        2: (deep, durations(25, 0.5, 1.2, 20.4)),
        3: (deep, durations(12, 0.6, 1.5, 13.0)),
        4: (anywhere, [10.0] * 8),
    }

    def edit(events):
        for slot, label in EVENT_LABELS.items():
            events.set_label(slot, label)
        for slot, (candidates, durs) in plan.items():
            events.add(slot, spans(free(candidates, len(durs)), durs))

    ui.edit_events(edit)


def boot(general=None, channels=None, events=False, size=(1500, 900)):
    """App on a temp copy of example_data at epoch EPOCH. `general`: dict merged into the
    general config; `channels`: fn(index, channel_config) editing each channel's config; `events`: seed example events."""
    directory = tempfile.mkdtemp(prefix="screenshots_")
    _copy_example(EXAMPLE_DIR, directory)
    shutil.copy(os.path.join(ROOT, "spectral.txt"), directory)  # the report colormap, found via ui.app_path
    cache = os.path.join(directory, "example_data.cache.pkl")  # the tracked one may predate the code
    if os.path.exists(cache):
        os.remove(cache)
    path = os.path.join(directory, "example_data.config.json")
    with open(path) as f:
        config = json.load(f)
    config[0].update({"Wavelet_display_mode": "dB (median baseline)", **(general or {})})
    for i, channel in enumerate(config[1]):
        channel["Line_width"] = 1.5
        if channels:
            channels(i, channel)
    config[1].sort(key=lambda ch: ch["Channel_name"] == "O2-A1")  # O2-A1 listed last, as in the screenshots
    with open(path, "w") as f:
        json.dump(config, f)

    app, window, ui = _boot(directory)
    add_symbol_fonts()
    window.resize(*size)
    window.show()
    from utilities.jump_to_epoch import jump_to_epoch

    if events:
        seed_events(ui)
    jump_to_epoch(EPOCH, ui)
    settle()
    ui._window, ui._directory = window, directory
    return ui


def add_symbol_fonts():
    """The offscreen platform has no system font fallback, so the 'trash' and 'info' glyphs
    the app draws as text would be empty boxes; register the OS symbol fonts when present."""
    from PySide6.QtGui import QFontDatabase

    for path in ("C:/Windows/Fonts/seguisym.ttf", "C:/Windows/Fonts/seguiemj.ttf",
                 "/System/Library/Fonts/Apple Symbols.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(path):
            QFontDatabase.addApplicationFont(path)


def settle():
    app = QApplication.instance()
    for _ in range(5):
        app.processEvents()


def close(ui):
    with mock.patch.object(QMessageBox, "exec", lambda self: QMessageBox.Yes):
        ui._window.close()
    settle()
    shutil.rmtree(ui._directory, ignore_errors=True)


def import_comparison(ui):
    """Run the app's own Compare > Scoring > Import with the file dialogs answered."""
    from scoring import scoring_import_comparison as module

    with mock.patch.object(module._FormatDialog, "exec", lambda self: True), \
            mock.patch.object(QFileDialog, "getOpenFileName", lambda *a, **k: (COMPARISON_FILE, "")):
        module.scoring_import_comparison(ui)
    settle()


# ---- drawables: (size, paint(painter)) ----------------------------------------------


def widget(w, rect=None):
    """The widget (or a rect of it, in widget coordinates) as it is on screen."""
    w.show()
    settle()
    rect = rect or w.rect()
    return rect.size(), lambda p: QWidget.render(w, p, QPoint(0, 0), QRegion(rect))  # not w.render: QGraphicsView overrides it


def region_of(parent, *children):
    """Rect in `parent` covering all `children`."""
    rect = QRect()
    for child in children:
        rect = rect.united(QRect(child.mapTo(parent, QPoint(0, 0)), child.size()))
    return rect


def write(name, drawable):
    size, paint = drawable
    os.makedirs(OUT_DIR, exist_ok=True)

    image = QImage(size, QImage.Format_ARGB32)
    image.fill(QColor("white"))
    painter = QPainter(image)
    paint(painter)
    painter.end()
    image.save(os.path.join(OUT_DIR, f"{name}.png"))

    svg = QSvgGenerator()
    svg.setFileName(os.path.join(OUT_DIR, f"{name}.svg"))
    svg.setSize(size)
    svg.setViewBox(QRect(QPoint(0, 0), size))
    svg.setResolution(round(QGuiApplication.primaryScreen().logicalDotsPerInch()))
    painter = QPainter(svg)
    painter.fillRect(QRect(QPoint(0, 0), size), QColor("white"))
    paint(painter)
    painter.end()
    print(f"{name}: {size.width()}x{size.height()}")


# ---- screenshots --------------------------------------------------------------------
# Each is a generator: boots what it needs, yields one drawable, cleans up when closed
# (the drawable is only valid until then, so it is drawn at the yield).

SHOTS = {}


def shot(fn):
    SHOTS[fn.__name__] = fn
    return fn


def panel(name, pick, **boot_kwargs):
    """Shot of the region of the main window covering the widgets `pick(ui)` returns. The
    region is rendered from the central widget, so overlays (stage badge, channel pills) show."""

    def run():
        ui = boot(**boot_kwargs)
        try:
            yield widget(ui.centralwidget, region_of(ui.centralwidget, *pick(ui)))
        finally:
            close(ui)

    run.__name__ = name
    SHOTS[name] = run


panel("signal_panel", lambda ui: [ui.SignalWidget.axes])
panel("spectrogram_panel", lambda ui: [ui.SpectogramWidget.graphics])
panel("periodogram_panel", lambda ui: [ui.RectanglePower.axes])
panel("wavelet_panel", lambda ui: [ui.TFWidget.graphics])
panel("hypnogram_panel", lambda ui: [ui.HypnogramWidget.axes, ui.HypnogramSlider])
panel("signal_stacked", lambda ui: [ui.SignalWidget.axes], general={"Stack_channels": True})
panel(
    "signal_zscore", lambda ui: [ui.SignalWidget.axes], general={"Robust_z_standardize": True},
    channels=lambda i, ch: ch.update(Display_on_screen=ch["Channel_name"] in ("F3-A2", "C3-A2", "EOG1")),
)


@shot
def main():
    ui = boot()
    try:
        yield widget(ui._window)
    finally:
        close(ui)


@shot
def events_on_signal():
    ui = boot()
    try:
        def edit(events):
            events.add(0, [(2972.5, 2975.0)])
            events.add(1, [(2977.0, 2978.2), (2992.0, 2993.0)])
            events.add(2, [(2982.0, 2983.2)])
            events.add(3, [(2996.0, 2998.0)])

        ui.edit_events(edit)
        from utilities.refresh_gui import refresh_gui

        refresh_gui(ui)
        settle()
        yield widget(ui.centralwidget, region_of(ui.centralwidget, ui.SignalWidget.axes))
    finally:
        close(ui)


@shot
def stage_badge():
    """Every badge state in a row: five stages, unscored, and a disagreement."""
    from widgets.stageBadge import StageBadge

    ui = boot(events=False)
    try:
        strip = QWidget()
        strip.resize(843, 58)
        strip.setStyleSheet("background: white;")
        states = [("Wake", None), ("N1", None), ("N2", None), ("N3", None), ("REM", None),
                  ("Unscored", None), ("N2", "N3")]
        badges = []
        for stage, other in states:
            badge = StageBadge(strip)
            badge.show_stage(stage, other, disagrees=other is not None, size=24)
            badges.append(badge)
        margin = 24
        gap = (strip.width() - 2 * margin - sum(b.width() for b in badges)) / (len(badges) - 1)
        x = margin
        for (stage, other), badge in zip(states, badges):
            center = (x + badge.width() / 2) / strip.width()
            badge.show_stage(stage, other, disagrees=other is not None, position=(center, 0.5), size=24)
            badge.show()
            x += badge.width() + gap
        yield widget(strip)
    finally:
        close(ui)


def _compare(ui):
    import_comparison(ui)
    return ui


@shot
def compare_hypnogram():
    ui = _compare(boot())
    try:
        yield widget(ui.centralwidget, region_of(ui.centralwidget, ui.HypnogramWidget.axes, ui.HypnogramSlider))
    finally:
        close(ui)


@shot
def compare_scoring():
    from scoring.comparison_stats_window import comparison_stats_window

    ui = _compare(boot())
    shown = []

    def fake_exec(self):
        shown.append(self)
        return 0

    try:
        with mock.patch.object(QDialog, "exec", fake_exec):
            comparison_stats_window(ui)
        shown[0].resize(680, 440)
        yield widget(shown[0])
    finally:
        close(ui)


def _filter_config(i, ch):
    if i < 4:
        ch.update(Filter_hp_enabled=True, Filter_notch_enabled=True, Filter_lp_cutoff=35.0)
    if i < 2:
        ch["Filter_lp_enabled"] = True


@shot
def filter():
    from filter.open_filter_window import open_filter_window

    ui = boot(channels=_filter_config)
    try:
        open_filter_window(ui)
        window = ui.FilterWindow
        window._plot_filter_response("lp", 0)
        plot = window.findChildren(QDialog)[-1]
        settle()
        size = QSize(window.width(), window.height() + plot.height() + 20)

        def paint(p):
            p.fillRect(QRect(QPoint(0, 0), size), QColor(229, 229, 229))
            QWidget.render(window, p, QPoint(0, 0))
            QWidget.render(plot, p, QPoint((window.width() - plot.width()) // 2, window.height() + 10))

        yield size, paint
    finally:
        close(ui)


def config_tab(name, tab):
    def run():
        from config.open_config_window import open_config_window

        ui = boot(events=True)
        try:
            open_config_window(ui)
            window = ui.ConfigurationWindow
            window.resize(796, 642)
            window.tabs.setCurrentIndex(tab)
            yield widget(window)
        finally:
            close(ui)

    run.__name__ = name
    SHOTS[name] = run


config_tab("general_config", 0)
config_tab("channel_config", 1)
config_tab("event_config", 2)


def detector(name, opener, window_attr, marker_slot):
    def run():
        import importlib

        ui = boot()
        try:
            getattr(importlib.import_module(opener[0]), opener[1])(ui)
            window = getattr(ui, window_attr)
            window._marker.setCurrentIndex(marker_slot)
            yield widget(window)
        finally:
            close(ui)

    run.__name__ = name
    SHOTS[name] = run


detector("mt_kcd", ("event_detection.open_mt_kcd_window", "open_mt_kcd_window"), "MtKcdWindow", 2)
detector("mt_spindle", ("event_detection.open_mt_spindle_window", "open_mt_spindle_window"), "MtSpindleWindow", 1)


@shot
def GSSC():
    from widgets import GsscWindow

    labels = [c["Channel_name"] for c in _channel_names()]
    window = GsscWindow(labels)
    for i in (2, 3):
        window._eeg_checkboxes[i].setChecked(True)
    for i in (5, 6):
        window._eog_checkboxes[i].setChecked(True)
    window.show()
    settle()
    window.findChildren(QScrollArea)[1].verticalScrollBar().setValue(10**6)
    yield widget(window)


@shot
def NIDRA():
    from widgets import NidraWindow

    window = NidraWindow([c["Channel_name"] for c in _channel_names()])
    yield widget(window)


def _channel_names():
    with open(os.path.join(EXAMPLE_DIR, "example_data.config.json")) as f:
        return json.load(f)[1]


@shot
def report_page():
    """Page 1 of the sleep report PDF (default options), rendered at 130 dpi."""
    from export import export_sleep_report as report

    ui = boot()
    try:
        options = report._ReportOptionsDialog(ui).get_options()
        pdf = os.path.join(ui._directory, "report.pdf")
        report._create_pdf_report(
            pdf,
            report._create_hypnogram(ui, options),
            report._create_whole_night_spectrogram(ui),
            None,
            report._calculate_sleep_statistics(ui.scoring, options),
            options["filename"],
        )
        document = QPdfDocument()
        document.load(pdf)
        image = document.render(0, QSize(1105, 1430))
        document.close()
        yield image.size(), lambda p: p.drawImage(0, 0, image)
    finally:
        close(ui)


# ---- main ---------------------------------------------------------------------------


def main_cli():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("names", nargs="*", help="screenshots to build (default: all)")
    parser.add_argument("--list", action="store_true", help="print the names and exit")
    args = parser.parse_args()
    if args.list:
        print("\n".join(SHOTS))
        return
    unknown = [n for n in args.names if n not in SHOTS]
    if unknown:
        parser.error(f"unknown: {', '.join(unknown)} (see --list)")
    for name in args.names or SHOTS:
        shot_run = SHOTS[name]()
        write(name, next(shot_run))
        shot_run.close()  # runs the shot's cleanup after it was drawn


if __name__ == "__main__":
    main_cli()
