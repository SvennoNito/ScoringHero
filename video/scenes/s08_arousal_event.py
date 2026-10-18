"""Scene 8: draw a real Arousal event in Epoch 137 (4083-4090 s), move it to another Event
slot by holding that slot's hotkey and clicking the event, wait 1 s, then delete it with a plain click.
"""

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

EPOCH = 136  # 0-based: Epoch 137
START_S = 4083.0
END_S = 4090.0
SLOT_1 = 1  # the slot the event is first drawn into (the spindle slot from scene 6)
SLOT_2 = 2  # the slot it is moved to, then deleted from
HOTKEY_1 = Qt.Key(Qt.Key_F1 + SLOT_1 - 1)  # Event hotkeys F1, F2, ... belong to slots 1, 2, ...
HOTKEY_2 = Qt.Key(Qt.Key_F1 + SLOT_2 - 1)


def _signal_x(ctx, seconds):
    """Window x of a time in the displayed Epoch."""
    paint = ctx.ref("PaintEventWidget")
    scene = ctx.ref("SignalWidget.axes").plotItem.vb.mapViewToScene(QPointF(seconds, 0))
    return paint.mapTo(ctx.window, paint.rect().topLeft()).x() + round(scene.x())


def _paint_y(ctx, fraction):
    paint = ctx.ref("PaintEventWidget")
    return paint.mapTo(ctx.window, paint.rect().topLeft()).y() + round(paint.height() * fraction)


def _install_key_filter(ctx):
    """The Event hotkeys live in the app-wide key filter that scoringhero.main() installs; the headless boot has none."""
    if "key_filter" not in ctx.state:
        import scoringhero as sh

        ctx.state["key_filter"] = sh.GlobalKeyFilter(ctx.ui, ctx.app)
        ctx.app.installEventFilter(ctx.state["key_filter"])


def run(ctx):
    ui = ctx.ui
    _install_key_filter(ctx)
    ctx.wait_idle()

    start, end = START_S, END_S
    print(f"s08: arousal drawn in Epoch {EPOCH + 1} ({start:.2f}-{end:.2f} s)", flush=True)

    # The hotkey add merges overlapping/touching spans (this real arousal location sits on top
    # of an auto-detected spindle), so the slot count does not simply go up by one: work out how
    # many existing spans the new rectangle will absorb to predict the post-add count.
    absorbed = sum(1 for s0, s1 in ui.events.spans(SLOT_1) if s0 <= end and s1 >= start)
    ctx.state.update(
        s08_epoch=EPOCH,
        s08_slot1_before=ui.events.count(SLOT_1),
        s08_slot2_before=ui.events.count(SLOT_2),
        s08_slot1_add_delta=1 - absorbed,
    )

    ctx.caption(f"An arousal in Epoch {EPOCH + 1}: go there")
    ctx.click_epoch(EPOCH, duration=1.0)
    ctx.wait(1.0)

    ctx.caption("Draw a rectangle around it, then press the Event hotkey")
    y0, y1 = _paint_y(ctx, 0.35), _paint_y(ctx, 0.75)  # below the paint overlay's length label
    ctx.drag(QPoint(_signal_x(ctx, start), y0), QPoint(_signal_x(ctx, end), y1), duration=1.0)
    assert ui.PaintEventWidget.stored_corners, "the rectangle was not drawn"
    ctx.wait(0.8)
    ctx.press_key(HOTKEY_1, seconds=1.0)
    ctx.state["s08_slot1_after_add"] = ui.events.count(SLOT_1)
    ctx.wait(1.0)

    ctx.caption(f"Move it to slot {SLOT_2}: hold its hotkey and click the event")
    middle = (start + end) / 2
    point = QPoint(_signal_x(ctx, middle), _paint_y(ctx, 0.5))
    widget = QApplication.focusWidget() or ctx.window
    QTest.keyPress(widget, HOTKEY_2)
    ctx.app.processEvents()
    ctx.wait(0.3)
    ctx.click(point, duration=0.8)
    QTest.keyRelease(widget, HOTKEY_2)
    ctx.app.processEvents()
    ctx.state.update(
        s08_slot1_after_move=ui.events.count(SLOT_1),
        s08_slot2_after_move=ui.events.count(SLOT_2),
    )
    ctx.wait(1.0)

    ctx.caption("Click the event to delete it")
    ctx.click(point, duration=1.0)
    ctx.state["s08_slot2_after_delete"] = ui.events.count(SLOT_2)
    ctx.wait(1.0)
    ctx.caption(None)


def check(ctx):
    ui, state = ctx.ui, ctx.state
    expected_after_add = state["s08_slot1_before"] + state["s08_slot1_add_delta"]
    assert state["s08_slot1_after_add"] == expected_after_add, \
        f"slot {SLOT_1} count after add: {state['s08_slot1_after_add']}, expected {expected_after_add}"
    assert state["s08_slot1_after_move"] == state["s08_slot1_after_add"] - 1, \
        f"slot {SLOT_1} count after move: {state['s08_slot1_after_move']}, expected {state['s08_slot1_after_add'] - 1}"
    assert state["s08_slot2_after_move"] == state["s08_slot2_before"] + 1, \
        f"slot {SLOT_2} count after move: {state['s08_slot2_after_move']}, expected {state['s08_slot2_before'] + 1}"
    assert state["s08_slot2_after_delete"] == state["s08_slot2_before"], \
        f"slot {SLOT_2} count after delete: {state['s08_slot2_after_delete']}, expected {state['s08_slot2_before']}"
    assert not ui.PaintEventWidget.stored_corners, "rectangles are left on the paint overlay"
