"""Scene 4: open the filter window, preview the magnitude response, then apply a 0.8 Hz high-pass Cutoff frequency."""

import pyqtgraph as pg
from make_video import ease
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QPushButton

CUTOFF_HZ = 0.8
DECIMAL_KEYS = {".": Qt.Key_Period, ",": Qt.Key_Comma}
ZOOM_HZ = 2.0
ZOOM_SECONDS = 0.8


def run(ctx):
    ctx.caption("Open the filter window to high-pass the Displayed signal")
    ctx.click_menu("action_filter")
    window = ctx.ref("FilterWindow")
    ctx.wait(0.8)

    ctx.caption(f"Set a {CUTOFF_HZ} Hz Cutoff frequency for all channels, then apply")
    ctx.click(ctx.at(window.apply_all_checkbox, 0.03, 0.5))  # the label, not the empty stretch, is clickable
    cutoff = window._fields["Filter_hp_cutoff"][0]
    ctx.click(cutoff)
    cutoff.setFocus()
    cutoff.selectAll()
    decimal_key = DECIMAL_KEYS[cutoff.locale().decimalPoint()]
    for key in [Qt.Key_Delete, Qt.Key_0, decimal_key, Qt.Key_8]:
        ctx.press_key(key, seconds=0.25)
    ctx.press_key(Qt.Key_Tab, seconds=0.2)
    ctx.click(window._fields["Filter_hp_enabled"][0])
    ctx.wait(0.6)

    ctx.caption("Preview the high-pass magnitude response before applying")
    hp_plt = next(
        b for b in window.findChildren(QPushButton) if b.toolTip() == "Plot high-pass frequency response"
    )
    ctx.click(hp_plt)
    response_dialog = next(
        (d for d in window.findChildren(QDialog) if d.windowTitle() == "Filter frequency response" and d.isVisible()),
        None,
    )
    ctx.state["s04_response_dialog_opened"] = response_dialog is not None
    if response_dialog is not None:
        ctx.wait(1.0)
        win = response_dialog.findChild(pg.GraphicsLayoutWidget)
        p1, p2 = win.getItem(0, 0), win.getItem(1, 0)
        nyquist = window._sampling_rate / 2.0
        steps = max(1, round(ZOOM_SECONDS * ctx._fps))
        for i in range(1, steps + 1):
            x_max = nyquist + (ZOOM_HZ - nyquist) * ease(i / steps)
            p1.setXRange(0, x_max, padding=0)
            p2.setXRange(0, x_max, padding=0)
            ctx.frame()
        ctx.wait(3.0)
        response_dialog.close()
    else:
        ctx.wait(4.0)
    ctx.state["s04_response_dialog_closed"] = response_dialog is not None and not response_dialog.isVisible()
    ctx.wait(0.4)

    ctx.click(ctx.button(window, "Apply"))
    ctx.wait(0.8)
    window.hide()
    ctx.wait(1.0)


def check(ctx):
    channels = ctx.ui.config[1]
    assert channels, "no channels configured"
    assert ctx.state.get("s04_response_dialog_opened"), "high-pass magnitude-response dialog was not opened"
    assert ctx.state.get("s04_response_dialog_closed"), "high-pass magnitude-response dialog was not closed before Apply"
    for channel in channels:
        assert channel["Filter_hp_enabled"], f"high-pass not enabled on {channel['Channel_name']}"
        assert abs(channel["Filter_hp_cutoff"] - CUTOFF_HZ) < 1e-9, (
            f"{channel['Channel_name']}: cutoff {channel['Filter_hp_cutoff']} Hz, expected {CUTOFF_HZ}")
