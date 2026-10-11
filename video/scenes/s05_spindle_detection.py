"""Scene 5: run the Event detector for spindles (MT-Spindle) on C3-A2 with default values.

Hands over to later scenes (add / delete a spindle) through ctx.state:
    "spindle_slot"    Event slot holding the detections
    "spindles"        [[start_s, end_s], ...] detected spans, in time order
    "spindle_epochs"  0-based epochs of each span (same order; a list per span)
    "spindle_densest" 0-based epoch with the most spindles
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QApplication, QDialogButtonBox, QProgressDialog

CHANNEL = "C3-A2"
SPINDLE_SLOT = 1
LABEL = "Spindle"


def _progress_dialogs():
    return [w for w in QApplication.topLevelWidgets() if isinstance(w, QProgressDialog) and w.isVisible()]


def _list_item_point(ctx, list_widget, text):
    items = list_widget.findItems(text, Qt.MatchExactly)
    if not items:
        raise LookupError(f"no list entry '{text}'")
    list_widget.scrollToItem(items[0], QAbstractItemView.PositionAtCenter)
    QApplication.processEvents()  # scrollbar and viewport update before the item's rectangle is read
    return list_widget.viewport().mapToGlobal(list_widget.visualItemRect(items[0]).center()) - ctx._origin()


def run(ctx):
    ui = ctx.ui
    ctx.wait_until(lambda: not getattr(ui, "_busy_runners", None))  # the busy indicator swallows mouse input
    if ui.events.label(SPINDLE_SLOT) != LABEL:  # off camera: name the slot the detections go to
        ui.edit_events(lambda events: events.set_label(SPINDLE_SLOT, LABEL))

    ctx.caption("Event detector: spindles with MT-Spindle")
    ctx.click_menu("action_mt_spindle")
    dialog = ctx.ref("MtSpindleWindow")
    dialog.move(ctx.window.geometry().center() - dialog.rect().center())
    ctx.wait(0.8)

    ctx.caption(f"Channel {CHANNEL}, default values")
    ctx.click(_list_item_point(ctx, dialog._ch_list, CHANNEL), duration=0.8)
    assert dialog._ch_list.currentItem().text() == CHANNEL, f"{CHANNEL} not selected"

    combo = dialog._marker  # keys, not the drop-down: its popup is clamped to the 800 px offscreen screen
    ctx.move_cursor(combo, duration=0.8)
    combo.setFocus()
    while combo.currentIndex() != SPINDLE_SLOT:
        ctx.press_key(Qt.Key_Up if combo.currentIndex() > SPINDLE_SLOT else Qt.Key_Down, seconds=0.5)
    assert combo.currentText() == LABEL, "the Spindle Event marker was not chosen"
    ctx.wait(1.0)

    ok = dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok)
    ctx.click(ok, duration=0.8)  # detection runs inside this click
    ctx.processing_card("Detecting spindles…", 2.0, until=lambda: not _progress_dialogs())

    spans = ui.events.spans(SPINDLE_SLOT)
    epochs = ui.events.epochs(SPINDLE_SLOT)
    per_epoch = {}
    for covered in epochs:
        for epoch in covered:
            per_epoch[epoch] = per_epoch.get(epoch, 0) + 1
    densest = max(per_epoch, key=lambda e: (per_epoch[e], -e)) if per_epoch else None
    ctx.state.update(spindle_slot=SPINDLE_SLOT, spindles=spans, spindle_epochs=epochs, spindle_densest=densest)
    print(f"s05: {len(spans)} spindles detected on {CHANNEL}; densest epoch {densest} "
          f"({per_epoch.get(densest, 0)} spindles)", flush=True)

    if densest is not None:
        ctx.caption(f"{len(spans)} spindles detected")
        ctx.click(ctx.spectrogram_point(densest), duration=1.0)
        ctx.wait(2.0)


def check(ctx):
    ui, state = ctx.ui, ctx.state
    assert ui.events.count(SPINDLE_SLOT) > 0, "no spindles detected"
    assert state["spindles"] == ui.events.spans(SPINDLE_SLOT), "state does not match the detected spindles"
    assert len(state["spindle_epochs"]) == len(state["spindles"])
    assert state["spindle_densest"] is not None
    assert ui.this_epoch == state["spindle_densest"], "view did not jump to the densest spindle epoch"
    assert not ui.MtSpindleWindow.isVisible(), "the detector dialog is still open"
    assert not _progress_dialogs(), "the progress dialog is still open"
