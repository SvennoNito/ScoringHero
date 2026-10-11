"""Scene 3: open the filter window and apply a 0.5 Hz high-pass Cutoff frequency."""

from PySide6.QtCore import Qt

CUTOFF_HZ = 0.5
KEYS = [Qt.Key_0, Qt.Key_Period, Qt.Key_5]  # typed after clearing: "0.5"


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
    for key in [Qt.Key_Delete] + KEYS:
        ctx.press_key(key, seconds=0.25)
    ctx.press_key(Qt.Key_Tab, seconds=0.2)
    ctx.click(window._fields["Filter_hp_enabled"][0])
    ctx.wait(0.6)
    ctx.click(ctx.button(window, "Apply"))
    ctx.wait(0.8)
    window.hide()
    ctx.wait(1.0)


def check(ctx):
    channels = ctx.ui.config[1]
    assert channels, "no channels configured"
    for channel in channels:
        assert channel["Filter_hp_enabled"], f"high-pass not enabled on {channel['Channel_name']}"
        assert abs(channel["Filter_hp_cutoff"] - CUTOFF_HZ) < 1e-9, (
            f"{channel['Channel_name']}: cutoff {channel['Filter_hp_cutoff']} Hz, expected {CUTOFF_HZ}")
