"""Render the silent, captioned ScoringHero walk-through video (issue #55).

    uv run python video/make_video.py                  # video/scoringhero_walkthrough.mp4, 1920x1080, 30 fps
    uv run python video/make_video.py --smoke          # all scenes, 640x360, 6 fps, state asserted after each
    uv run python video/make_video.py --scenes s01     # only scenes whose module name starts with s01

The real main window is booted offscreen on a temp copy of example_data (tracked files are
never touched), with no recording loaded: the film opens on the empty window. The first scene
loads the recording through File > Load EEG, without its scoring sidecar: no Primary scoring,
no Events. Scenes drive the window with Qt mouse and key events through a drawn cursor; every
input step renders frames of the window.

Scene contract (add a scene = one new module + one line in video/scenes/__init__.py):

    # video/scenes/sNN_name.py
    def run(ctx):    # film the scene: caption + input steps through ctx
    def check(ctx):  # assert the app state the scene must have produced (raise AssertionError)

  * Scenes run in the order of `scenes.SCENES`, sharing one app and one ctx (`ctx.state` is a
    dict for handing data to later scenes and to `check`). `check` runs right after `run`, in
    smoke and full renders alike; any exception (failed lookup, failed assertion) aborts the run.
  * Find widgets by reference, never by pixel: `ctx.ref("A.b")` (dotted attribute path from `ui`),
    `ctx.named(objectName)`, `ctx.menu_action(attr)`. All raise LookupError on failure.
  * Input helpers (positions are window coordinates, targets are a QPoint or a QWidget's
    centre): `move_cursor`, `click`, `click_epoch`, `drag`, `press_key`, `click_menu`, plus `center(widget)`,
    `at(widget, fx, fy)`, `window_point(widget, local_pt)` and `spectrogram_point(epoch)`.
    Events go to the widget under the cursor. Finders: `button(dialog, text)`, `progress_dialogs()`.
  * Film helpers: `caption(text | None)`, `processing_card(text, seconds, until)` (runs the work
    off camera, shows a short card instead), `wait(seconds)`, `ctx.wait_until(cond)` and `ctx.wait_idle()` (off camera;
    call wait_idle before the first click of a scene: background work blocks mouse input).
  * Native dialogs: `with ctx.file_dialogs(open=(folder, filename, name_filter=None), save=path,
    directory=path):` answers the app's static QFileDialog calls and QMessageBox.exec (Yes).
    `open` drives `ctx.filmed_open_dialog(folder, filename, name_filter=None)`: it opens a
    real, non-native QFileDialog at `folder` (restricted to `name_filter` if given, e.g.
    "*.mat"), films it, clicks `filename` in the file list, then clicks Open, and returns the
    chosen path — this is what the viewer sees when the app loads a Recording (scene 1) or
    imports a Comparison scoring / Overlay signal (later scenes). `save`/`directory` still
    answer getSaveFileName/getExistingDirectory silently. Dialogs the app opens with its own
    `exec` (QDialog) would block the script: patch that class's `exec` in the scene, as
    make_screenshots.py does. Visible dialogs and menu popups are composited into the frames.
  * Durations are in seconds of video; smoke lowers fps, so scenes stay fast without changes.
  * Generated inputs (Comparison scoring, Overlay signal, report) go to `ctx.video_dir`
    (gitignored extensions: .mp4 .mat .json .pdf).
"""

import argparse
import contextlib
import importlib
import os
import shutil
import sys
import tempfile
import time
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

VIDEO_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(VIDEO_DIR)
sys.path.insert(0, ROOT)
sys.path.insert(0, VIDEO_DIR)

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QFontMetrics, QImage, QMouseEvent, QPainter, QPolygonF  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QFileDialog,
    QListView,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTreeView,
    QWidget,
)

from tests.conftest import EXAMPLE_DIR, _build  # noqa: E402

FULL = {"size": (1920, 1080), "fps": 30}
SMOKE = {"size": (640, 360), "fps": 6}
WINDOW_SIZE = (1920, 1080)  # the app is always laid out at full size; smoke only scales the frames
RIPPLE_SECONDS = 0.5


def ease(t):
    """Smooth start and stop (smootherstep) for t in [0, 1]."""
    return t * t * t * (t * (6 * t - 15) + 10)


SHOW_ORDER_PROPERTY = "_ctx_show_order"


class _ShowOrderTracker(QObject):
    """App-wide event filter: stamps every top-level widget with an incrementing sequence
    number the moment it receives QEvent.Show, so _stacking_order can sort by actual show
    order. Keying off a dynamic Qt property (stored on the widget itself) rather than a
    Python dict keyed by id() avoids stale entries: CPython can reuse a destroyed widget's id
    for an unrelated later widget, which would silently resurrect a stale sequence number."""

    def __init__(self):
        super().__init__()
        self._counter = 0

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Show and isinstance(watched, QWidget) and watched.isWindow():
            self._counter += 1
            watched.setProperty(SHOW_ORDER_PROPERTY, self._counter)
        return False


class Context:
    """What a scene sees: the app (`ui`, `window`) and the helpers listed in the module docstring."""

    def __init__(self, app, window, ui, directory, writer, size, fps):
        self.app, self.window, self.ui = app, window, ui
        self.directory = directory  # temp copy of the recording
        self.video_dir = VIDEO_DIR
        self.state = {}
        self._writer, self._size, self._fps = writer, size, fps
        self._frame = 0
        self._caption = None
        self._card = None
        self._ripples = []  # (start frame, x, y)
        self._show_tracker = _ShowOrderTracker()
        self.app.installEventFilter(self._show_tracker)
        self._cursor = QPointF(WINDOW_SIZE[0] / 2, WINDOW_SIZE[1] / 2)
        self.frames_written = 0

    # ---- finding widgets by reference ---------------------------------------------------

    def ref(self, path):
        """Object at the dotted attribute `path` of `ui` (e.g. "SpectogramWidget.graphics")."""
        obj = self.ui
        for part in path.split("."):
            obj = getattr(obj, part, None)
            if obj is None:
                raise LookupError(f"ui.{path}: '{part}' not found")
        return obj

    def named(self, object_name):
        """Widget with this objectName anywhere in the main window."""
        widget = self.window.findChild(QWidget, object_name)
        if widget is None:
            raise LookupError(f"no widget named '{object_name}'")
        return widget

    def menu_action(self, attribute):
        """(menus, action) for the QAction at `ui.<attribute>`: the chain of menus from the
        menu bar down to the menu holding it."""
        action = getattr(self.ui, attribute, None)
        if action is None:
            raise LookupError(f"ui.{attribute} not found")
        chain = self._menu_chain(self.ui.menu, action)
        if chain is None:
            raise LookupError(f"ui.{attribute} is in no menu")
        return chain, action

    def _menu_chain(self, parent, target):
        for action in parent.actions():
            if action is target:
                return []
            menu = action.menu()
            if menu is not None:
                found = self._menu_chain(menu, target)
                if found is not None:
                    return [menu] + found
        return None

    # ---- positions ---------------------------------------------------------------------

    def _origin(self):
        return self.window.mapToGlobal(QPoint(0, 0))

    def to_global(self, point):
        return self._origin() + QPoint(round(point.x()), round(point.y()))

    def window_point(self, widget, local_pt):
        """`local_pt` (a QPoint in `widget` coordinates) in window coordinates."""
        return widget.mapToGlobal(local_pt) - self._origin()

    def center(self, widget):
        """Centre of the widget, in window coordinates."""
        return self.at(widget, 0.5, 0.5)

    def at(self, widget, fx, fy):
        """Point at fractions (fx, fy) of the widget's size, in window coordinates."""
        return self.window_point(widget, QPoint(round(widget.width() * fx), round(widget.height() * fy)))

    def spectrogram_point(self, epoch, fy=0.5):
        """Window position of 0-based `epoch` in the spectrogram Panel (fy: fraction of the frequency range)."""
        view = self.ref("SpectogramWidget.axes").getViewBox()
        y_lo, y_hi = view.viewRange()[1]
        scene = view.mapViewToScene(QPointF(epoch + 0.5, y_lo + (1 - fy) * (y_hi - y_lo)))
        graphics = self.ref("SpectogramWidget.graphics")
        return graphics.viewport().mapTo(self.window, graphics.mapFromScene(scene))

    def _as_point(self, target):
        if isinstance(target, QWidget):
            return self.center(target)
        return QPoint(target)

    def _stacking_order(self):
        """Visible top-level windows in paint order (bottom to top): the main window first, then
        dialogs/menus ordered by show order (a window shown more recently paints in front of one
        shown earlier; re-showing an already-tracked window bumps it back to the front, via the
        `_ShowOrderTracker` event filter installed in `__init__`), then the active popup last
        (always topmost)."""
        popup = QApplication.activePopupWidget()
        tops = [w for w in QApplication.topLevelWidgets()
                if w.isVisible() and w is not self.window and w is not popup]

        tops.sort(key=lambda w: w.property(SHOW_ORDER_PROPERTY) or 0)
        order = [self.window] + tops
        if popup is not None and popup.isVisible():
            order.append(popup)
        return order

    def _widget_at(self, point):
        """Widget under `point` (window coordinates): the topmost window at that point, in
        reverse stacking order (popup first, then dialogs nearest the top, then the main window)."""
        global_point = self.to_global(point)
        for top in reversed(self._stacking_order()):
            if top.frameGeometry().contains(global_point) or top.geometry().contains(global_point):
                local = top.mapFromGlobal(global_point)
                child = top.childAt(local)
                return child or top
        raise LookupError(f"no widget at {point}")

    # ---- frames ------------------------------------------------------------------------

    def caption(self, text):
        """Show `text` (None clears) at the bottom of every following frame."""
        self._caption = text

    def _compose(self):
        self.app.processEvents()
        base = self.window.grab().toImage().convertToFormat(QImage.Format_RGB888)
        origin = self._origin()
        painter = QPainter(base)
        for top in self._stacking_order()[1:]:  # dialogs and menu popups, bottom to top
            painter.drawImage(top.pos() - origin, top.grab().toImage())
        self._paint_overlays(painter, base.width(), base.height())
        painter.end()
        return base

    def _paint_overlays(self, painter, width, height):
        painter.setRenderHint(QPainter.Antialiasing)
        if self._card is not None:
            painter.fillRect(0, 0, width, height, QColor(15, 20, 30, 215))
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Arial", 44))
            painter.drawText(QRectF(0, 0, width, height), Qt.AlignCenter, self._card)
        for start, x, y in self._ripples:
            t = (self._frame - start) / (RIPPLE_SECONDS * self._fps)
            if 0 <= t <= 1:
                radius = 8 + 38 * ease(t)
                painter.setPen(QColor(255, 190, 40, round(255 * (1 - t))))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(x, y), radius, radius)
        self._ripples = [r for r in self._ripples if self._frame - r[0] <= RIPPLE_SECONDS * self._fps]
        if self._caption:
            font = QFont("Arial", 30)
            painter.setFont(font)
            metrics = QFontMetrics(font)
            text_w = metrics.horizontalAdvance(self._caption)
            box = QRectF((width - text_w) / 2 - 32, height - 120, text_w + 64, 70)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(15, 20, 30, 215))
            painter.drawRoundedRect(box, 16, 16)
            painter.setPen(QColor("white"))
            painter.drawText(box, Qt.AlignCenter, self._caption)
        if self._card is None:
            self._paint_cursor(painter)

    def _paint_cursor(self, painter):
        arrow = QPolygonF([QPointF(0, 0), QPointF(0, 26), QPointF(6.5, 20), QPointF(11, 31),
                           QPointF(15, 29), QPointF(10.5, 19), QPointF(19, 19)])
        arrow.translate(self._cursor)
        painter.setPen(QColor("black"))
        painter.setBrush(QColor("white"))
        painter.drawPolygon(arrow)

    def frame(self):
        """Render and write one frame of the current state."""
        image = self._compose()
        if image.size().toTuple() != self._size:
            image = image.scaled(*self._size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self._writer.send(_packed(image))
        self._frame += 1
        self.frames_written += 1

    def wait(self, seconds):
        """Film `seconds` of the app as it is (animations, ripples, caption)."""
        for _ in range(max(1, round(seconds * self._fps))):
            self.frame()

    def wait_until(self, condition, timeout=300):
        """Process events (not filmed) until `condition()` holds."""
        end = time.time() + timeout
        while not condition() and time.time() < end:
            self.app.processEvents()
            time.sleep(0.01)
        if not condition():
            raise TimeoutError("condition not met in time")

    def wait_idle(self):
        """Process events (not filmed) until no background work is left: the busy indicator swallows mouse input."""
        self.wait_until(lambda: not getattr(self.ui, "_busy_runners", None))

    def processing_card(self, text="Processing…", seconds=2.0, until=None):
        """Run the app until `until()` (default: no background work left) off camera, then
        film a full-frame card with `text` for `seconds` instead of the wait."""
        if until:
            self.wait_until(until)
        else:
            self.wait_idle()
        self._card = text
        try:
            self.wait(seconds)
        finally:
            self._card = None

    # ---- input -------------------------------------------------------------------------

    def move_cursor(self, target, duration=0.8):
        """Glide the drawn cursor to `target` with eased motion, then hover there."""
        end = self._as_point(target)
        start = QPointF(self._cursor)
        steps = max(1, round(duration * self._fps))
        for i in range(1, steps + 1):
            t = ease(i / steps)
            self._cursor = start + (QPointF(end) - start) * t
            self.frame()
        self._send_mouse(QEvent.MouseMove, end, Qt.NoButton, Qt.NoButton)

    def _send_mouse(self, kind, point, button, buttons):
        widget = self._widget_at(point)
        local = QPointF(widget.mapFromGlobal(self.to_global(point)))
        event = QMouseEvent(kind, local, QPointF(self.to_global(point)), button, buttons, Qt.NoModifier)
        QApplication.sendEvent(widget, event)
        self.app.processEvents()

    def click(self, target, duration=0.8, button=Qt.LeftButton):
        """Move to `target`, ripple and press+release a mouse button on the widget under it."""
        self.move_cursor(target, duration)
        point = self._as_point(target)
        self._ripples.append((self._frame, point.x(), point.y()))
        self._send_mouse(QEvent.MouseButtonPress, point, button, button)
        self.wait(0.1)
        self._send_mouse(QEvent.MouseButtonRelease, point, button, Qt.NoButton)
        self.wait(0.2)

    def drag(self, start, end, duration=1.0, button=Qt.LeftButton):
        """Move to `start`, press, glide to `end` with the button held, release."""
        self.move_cursor(start, 0.8)
        begin, finish = self._as_point(start), self._as_point(end)
        self._send_mouse(QEvent.MouseButtonPress, begin, button, button)
        steps = max(1, round(duration * self._fps))
        for i in range(1, steps + 1):
            self._cursor = QPointF(begin) + QPointF(finish - begin) * ease(i / steps)
            self._send_mouse(QEvent.MouseMove, self._cursor.toPoint(), Qt.NoButton, button)
            self.frame()
        self._send_mouse(QEvent.MouseButtonRelease, finish, button, Qt.NoButton)
        self.wait(0.2)

    def press_key(self, key, modifier=Qt.NoModifier, seconds=0.4):
        """Press and release `key` (a Qt.Key) on the focused widget (main window if none)."""
        QTest.keyClick(QApplication.focusWidget() or self.window, key, modifier)
        self.app.processEvents()
        self.wait(seconds)

    def click_menu(self, attribute):
        """Walk the cursor down the menus to the QAction at `ui.<attribute>` and trigger it."""
        menus, action = self.menu_action(attribute)
        bar = self.ui.menu
        top = menus[0].menuAction()
        self.move_cursor(self.window_point(bar, bar.actionGeometry(top).center()), 0.7)
        bar.setActiveAction(top)
        self.wait(0.3)
        for parent, entry in zip(menus, menus[1:] + [None]):
            target = entry.menuAction() if entry is not None else action
            point = self.window_point(parent, parent.actionGeometry(target).center())
            self.move_cursor(point, 0.5)
            parent.setActiveAction(target)
            if entry is not None:
                entry.popup(parent.mapToGlobal(parent.actionGeometry(target).topRight()))
            self.wait(0.3)
        point = self._cursor.toPoint()
        self._ripples.append((self._frame, point.x(), point.y()))
        for menu in reversed(menus):
            menu.hide()
        action.trigger()
        self.app.processEvents()
        self.wait(0.3)

    def click_epoch(self, epoch, duration=0.9):
        """Click 0-based `epoch` in the spectrogram Panel and assert the view jumped there."""
        self.click(self.spectrogram_point(epoch), duration=duration)
        assert self.ui.this_epoch == epoch, f"click on Epoch {epoch} displayed Epoch {self.ui.this_epoch}"

    def button(self, dialog, text):
        """The push button of `dialog` labelled `text` (e.g. "OK", "Apply")."""
        for button in dialog.findChildren(QPushButton):
            if button.text().replace("&", "") == text:
                return button
        raise LookupError(f"no button '{text}' in {type(dialog).__name__}")

    def progress_dialogs(self):
        """Progress dialogs of the app that are showing."""
        return [w for w in self.app.topLevelWidgets() if isinstance(w, QProgressDialog) and w.isVisible()]

    def filmed_open_dialog(self, folder, filename, name_filter=None):
        """Open a real, non-native QFileDialog at `folder` (restricted to `name_filter` if
        given, e.g. "*.mat"), film it, click `filename` in the file list, then click Open.
        Returns the chosen path. Used by `file_dialogs(open=...)` to answer the app's static
        open-file calls with a visible, driven dialog instead of an instant silent answer."""
        dialog = QFileDialog(self.window, "Open File", folder, name_filter or "")
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setModal(False)
        dialog.show()
        for _ in range(5):
            self.app.processEvents()
        view = dialog.findChild(QTreeView, "treeView")
        if view is None or not view.isVisible():
            view = dialog.findChild(QListView, "listView")
        root = view.rootIndex()
        self.wait_until(lambda: view.model().rowCount(root) > 0)
        self.wait(0.6)
        index = None
        model = view.model()
        for row in range(model.rowCount(root)):
            candidate = model.index(row, 0, root)
            if model.data(candidate) == filename:
                index = candidate
                break
        if index is None:
            dialog.close()
            raise LookupError(f"'{filename}' not found in {folder}")
        self.click(self.window_point(view.viewport(), view.visualRect(index).center()))
        self.click(self.button(dialog, "Open"))
        path = os.path.join(folder, filename)
        dialog.close()
        return path

    @contextlib.contextmanager
    def file_dialogs(self, open=None, save=None, directory=None):
        """Answer the app's static dialog calls. `open`: a (folder, filename) or (folder,
        filename, name_filter) tuple — getOpenFileName/getOpenFileNames are answered by filming
        and driving a real dialog through `filmed_open_dialog`. `save`/`directory`: paths
        returned silently by getSaveFileName/getExistingDirectory. QMessageBox.exec always
        returns Yes."""
        def opened_path():
            folder, filename, *rest = open
            name_filter = rest[0] if rest else None
            return self.filmed_open_dialog(folder, filename, name_filter)

        with mock.patch.object(QFileDialog, "getOpenFileName", lambda *a, **k: (opened_path() if open else "", "")), \
                mock.patch.object(QFileDialog, "getOpenFileNames", lambda *a, **k: ([opened_path()] if open else [], "")), \
                mock.patch.object(QFileDialog, "getSaveFileName", lambda *a, **k: (save or "", "")), \
                mock.patch.object(QFileDialog, "getExistingDirectory", lambda *a, **k: directory or ""), \
                mock.patch.object(QMessageBox, "exec", lambda self: QMessageBox.Yes):
            yield


def _packed(image):
    """RGB bytes of the image without per-row padding (rows are 4-byte aligned; widths of 640 and 1920 have none)."""
    width = image.width() * 3
    data = bytes(image.constBits())
    if image.bytesPerLine() == width:
        return data
    return b"".join(data[y * image.bytesPerLine(): y * image.bytesPerLine() + width] for y in range(image.height()))


def boot():
    """Bare app window on a temp copy of the example recording files (no scoring sidecar), in a
    temp folder named to read clearly in the filmed file dialog ("...ScoringHero example"); no
    recording is loaded yet — the first scene loads it through File > Load EEG."""
    directory = tempfile.mkdtemp(suffix=" - ScoringHero example")
    for name in os.listdir(EXAMPLE_DIR):
        stem = "example_data"
        if name.startswith(stem + ".") and name != stem + ".json":
            shutil.copy(os.path.join(EXAMPLE_DIR, name), directory)
    shutil.copy(os.path.join(ROOT, "spectral.txt"), directory)  # the report colormap, found via ui.app_path
    cache = os.path.join(directory, "example_data.cache.pkl")  # the tracked one may predate the code
    if os.path.exists(cache):
        os.remove(cache)

    app, window, ui = _build(directory)
    window.resize(*WINDOW_SIZE)
    window.show()
    for _ in range(5):
        app.processEvents()
    return app, window, ui, directory


def assert_empty_start(ui):
    assert not any(ui.scoring.stages()), "Primary scoring is not empty at the start"
    assert not any(ui.events.count(s) for s in range(len(ui.events.labels()))), "Events are not empty at the start"


def load_scenes(prefixes):
    import scenes

    names = [n for n in scenes.SCENES if not prefixes or any(n.startswith(p) for p in prefixes)]
    if not names:
        raise SystemExit(f"no scene matches {prefixes}; available: {scenes.SCENES}")
    return [(n, importlib.import_module(f"scenes.{n}")) for n in names]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--smoke", action="store_true", help="low resolution and fps; every scene is checked")
    parser.add_argument("--scenes", nargs="*", default=[], help="only scenes whose module name starts with one of these")
    parser.add_argument("--out", help="output mp4 (default video/scoringhero_walkthrough.mp4, video/smoke.mp4 with --smoke)")
    args = parser.parse_args()
    mode = SMOKE if args.smoke else FULL
    out = args.out or os.path.join(VIDEO_DIR, "smoke.mp4" if args.smoke else "scoringhero_walkthrough.mp4")
    scenes = load_scenes(args.scenes)

    import imageio_ffmpeg

    app, window, ui, directory = boot()
    writer = imageio_ffmpeg.write_frames(out, mode["size"], fps=mode["fps"], quality=8, macro_block_size=1)
    writer.send(None)
    ctx = Context(app, window, ui, directory, writer, mode["size"], mode["fps"])
    started = time.time()
    try:
        ctx.wait(1.0)
        for name, module in scenes:
            began = time.time()
            module.run(ctx)
            module.check(ctx)
            print(f"{name}: ok ({time.time() - began:.1f} s, {ctx.frames_written} frames)", flush=True)
    finally:
        writer.close()
        with mock.patch.object(QMessageBox, "exec", lambda self: QMessageBox.Yes):
            window.close()
        app.processEvents()
        shutil.rmtree(directory, ignore_errors=True)
    print(f"wrote {out}: {ctx.frames_written / mode['fps']:.1f} s of video in {time.time() - started:.0f} s")


if __name__ == "__main__":
    main()
