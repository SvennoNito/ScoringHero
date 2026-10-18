"""Scene 6: run the Event detector for spindles (MT-Spindle) on C3-A2 with default values.

Hands over to later scenes (Events tab rename, periodogram) through ctx.state:
    "spindles"        [[start_s, end_s], ...] detected spans, in time order
    "spindle_epochs"  0-based epochs of each span (same order; a list per span)
    "spindle_densest" 0-based epoch with the most spindles
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QApplication

CHANNEL = "C3-A2"
SPINDLE_SLOT = 1


def _list_item_point(ctx, list_widget, text):
    items = list_widget.findItems(text, Qt.MatchExactly)
    if not items:
        raise LookupError(f"no list entry '{text}'")
    list_widget.scrollToItem(items[0], QAbstractItemView.PositionAtCenter)
    QApplication.processEvents()  # scrollbar and viewport update before the item's rectangle is read
    return ctx.window_point(list_widget.viewport(), list_widget.visualItemRect(items[0]).center())


def run(ctx):
    ui = ctx.ui
    ctx.wait_idle()

    ctx.caption("Event detector: spindles with MT-Spindle")
    ctx.click_menu("action_mt_spindle")
    dialog = ctx.ref("MtSpindleWindow")
    dialog.move(ctx.window.geometry().center() - dialog.rect().center())
    ctx.wait(0.8)

    ctx.caption(f"Channel {CHANNEL}, default values")
    ctx.click(_list_item_point(ctx, dialog._ch_list, CHANNEL), duration=0.8)
    assert dialog._ch_list.currentItem().text() == CHANNEL, f"{CHANNEL} not selected"

    combo = dialog._marker
    ctx.move_cursor(combo, duration=0.8)
    combo.setFocus()
    combo.showPopup()
    ctx.wait(1.0)  # hold open, showing the Event marker options
    combo.setCurrentIndex(SPINDLE_SLOT)
    assert combo.currentText() == "F1", "the F1 Event marker was not chosen"
    ctx.wait(0.5)  # hold open, showing F1 chosen
    combo.hidePopup()
    ctx.wait(0.5)

    ctx.click(ctx.button(dialog, "OK"), duration=0.8)  # detection runs inside this click
    ctx.processing_card("Detecting spindles…", 2.0, until=lambda: not ctx.progress_dialogs())

    spans = ui.events.spans(SPINDLE_SLOT)
    epochs = ui.events.epochs(SPINDLE_SLOT)
    per_epoch = {}
    for covered in epochs:
        for epoch in covered:
            per_epoch[epoch] = per_epoch.get(epoch, 0) + 1
    densest = max(per_epoch, key=lambda e: (per_epoch[e], -e)) if per_epoch else None
    ctx.state.update(spindles=spans, spindle_epochs=epochs, spindle_densest=densest)
    print(f"s06: {len(spans)} spindles detected on {CHANNEL}; densest epoch {densest} "
          f"({per_epoch.get(densest, 0)} spindles)", flush=True)

    if densest is not None:
        ctx.caption(f"{len(spans)} spindles detected")
        ctx.click_epoch(densest, duration=1.0)
        ctx.wait(2.0)


def check(ctx):
    ui, state = ctx.ui, ctx.state
    assert ui.events.count(SPINDLE_SLOT) > 0, "no spindles detected"
    assert state["spindles"] == ui.events.spans(SPINDLE_SLOT), "state does not match the detected spindles"
    assert len(state["spindle_epochs"]) == len(state["spindles"])
    assert state["spindle_densest"] is not None
    assert ui.this_epoch == state["spindle_densest"], "view did not jump to the densest spindle epoch"
    assert not ui.MtSpindleWindow.isVisible(), "the detector dialog is still open"
    assert not ctx.progress_dialogs(), "the progress dialog is still open"
