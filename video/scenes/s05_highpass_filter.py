"""Scene 3: open the filter window, preview the magnitude response, then apply a 0.5 Hz high-pass Cutoff frequency."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QPushButton

CUTOFF_HZ = 0.5
DECIMAL_KEYS = {".": Qt.Key_Period, ",": Qt.Key_Comma}


def run(ctx):
    ctx.caption("Open the filter window to high-pass the Displayed signal")
    ctx.click_menu("action_filter")
    window = ctx.ref("FilterWindow")
    ctx.wait(0.8)

    ctx.caption("Set a 0.5 Hz Cutoff frequency for all channels, then apply")
    ctx.click(ctx.at(window.apply_all_checkbox, 0.03, 0.5))  # the label, not the empty stretch, is clickable
    cutoff = window._fields["Filter_hp_cutoff"][0]
    ctx.click(cutoff)
    cutoff.setFocus()
    cutoff.selectAll()
    decimal_key = DECIMAL_KEYS[cutoff.locale().decimalPoint()]
    for key in [Qt.Key_Delete, Qt.Key_0, decimal_key, Qt.Key_5]:
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
    ctx.state["s05_response_dialog_opened"] = response_dialog is not None
    ctx.wait(3.0)
    if response_dialog is not None:
        response_dialog.close()
    ctx.state["s05_response_dialog_closed"] = response_dialog is not None and not response_dialog.isVisible()
    ctx.wait(0.4)

    ctx.click(ctx.button(window, "Apply"))
    ctx.wait(0.8)
    window.hide()
    ctx.wait(1.0)


def check(ctx):
    channels = ctx.ui.config[1]
    assert channels, "no channels configured"
    assert ctx.state.get("s05_response_dialog_opened"), "high-pass magnitude-response dialog was not opened"
    assert ctx.state.get("s05_response_dialog_closed"), "high-pass magnitude-response dialog was not closed before Apply"
    for channel in channels:
        assert channel["Filter_hp_enabled"], f"high-pass not enabled on {channel['Channel_name']}"
        assert abs(channel["Filter_hp_cutoff"] - CUTOFF_HZ) < 1e-9, (
            f"{channel['Channel_name']}: cutoff {channel['Filter_hp_cutoff']} Hz, expected {CUTOFF_HZ}")
