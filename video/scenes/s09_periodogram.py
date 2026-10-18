"""Scene 9: draw a transient selection rectangle (NOT an Event: no hotkey) centred on the
C3-A2 trace's row over one detected spindle, showing that the Periodogram panel (RectanglePower)
displays the row the rectangle overlaps -- not whatever channel Configuration > Periodogram has
set (Periodogram_channel defaults to a different channel in example_data).

Mechanics (paint_event/paint_event_handler.py, widgets/paintEventWidget.py,
signal_processing/channel_from_selection.py, signal_processing/compute_periodogram.py):
drawing a rectangle on the PaintEventWidget overlay (the same drag-on-signal-panel mechanism
Events use) fires `changesMade` on mouse release, which runs paint_event_handler(ui) even
if no hotkey ever commits the rectangle as an Event. That handler picks the channel whose
plotted row the rectangle's vertical midpoint is closest to (channel_from_selection, using
each visible channel's Vertical_shift / Distance_between_channels_muV anchor), extracts that
channel's samples under the rectangle, computes a Welch periodogram, and calls
ui.RectanglePower.update_powerline(freqs, power, channel_name). That channel only changes again
on the next redraw/navigation (refresh_gui/redraw_gui), which falls back to
ui.config[0]["Periodogram_channel"] (the Configuration > Periodogram combo) via
compute_epoch_periodogram -- a separate, config-driven code path used for epoch navigation,
not for the rectangle-drag selection this scene exercises.
"""

from PySide6.QtCore import QPoint, QPointF

CHANNEL = "C3-A2"
SPINDLE_SLOT = 1
HALF_HEIGHT_MUV = 30.0


def _window_point(ctx, seconds, amplitude):
    vb = ctx.ref("SignalWidget.axes").plotItem.vb
    scene_pt = vb.mapViewToScene(QPointF(seconds, amplitude))
    paint = ctx.ref("PaintEventWidget")
    origin = paint.mapTo(ctx.window, paint.rect().topLeft())
    return QPoint(origin.x() + round(scene_pt.x()), origin.y() + round(scene_pt.y()))


def _channel_index(ui, name):
    for i, info in enumerate(ui.config[1]):
        if info["Channel_name"] == name:
            return i
    raise LookupError(f"no channel named '{name}'")


def _channel_anchor(ui, channel_idx):
    """Window-coordinate-free amplitude anchor of a channel's row, matching
    signal_processing/channel_from_selection.py's channel_anchors formula exactly."""
    visible = [i for i, info in enumerate(ui.config[1]) if info["Display_on_screen"]]
    numchans_visible = len(visible)
    pos = visible.index(channel_idx)
    return (
        ui.config[1][channel_idx]["Vertical_shift"]
        - ui.config[0]["Distance_between_channels_muV"] * numchans_visible * pos
    )


def _choose_spindle(state):
    """(start_s, end_s, epoch) of a detected spindle whose span sits fully inside one epoch."""
    for span, epochs in zip(state["spindles"], state["spindle_epochs"]):
        if len(epochs) == 1:
            return span[0], span[1], epochs[0]
    # fall back to the densest epoch's first spindle if every span straddles an epoch edge
    densest = state["spindle_densest"]
    for span, epochs in zip(state["spindles"], state["spindle_epochs"]):
        if densest in epochs:
            return span[0], span[1], densest
    raise RuntimeError("no spindle available to select")


def run(ctx):
    ui = ctx.ui
    ctx.wait_idle()

    start_s, end_s, epoch = _choose_spindle(ctx.state)
    ctx.state["s09_count_before"] = ui.events.count(SPINDLE_SLOT)
    ctx.state["s09_periodogram_channel_config"] = ui.config[0]["Periodogram_channel"]

    ctx.caption(f"Jump to the spindle at epoch {epoch + 1}")
    ctx.click_epoch(epoch, duration=0.9)
    ctx.wait(0.5)

    channel_idx = _channel_index(ui, CHANNEL)
    anchor = _channel_anchor(ui, channel_idx)
    start_pt = _window_point(ctx, start_s, anchor - HALF_HEIGHT_MUV)
    end_pt = _window_point(ctx, end_s, anchor + HALF_HEIGHT_MUV)

    ctx.caption(f"Draw a selection over {CHANNEL} only (not committed as an Event)")
    ctx.drag(start_pt, end_pt, duration=1.0)
    assert ui.PaintEventWidget.stored_corners, "the selection rectangle was not drawn"
    ctx.wait(0.3)

    ctx.caption("Periodogram panel: power spectrum of that selection")
    ctx.state["s09_channel_shown"] = ui.RectanglePower.channel_pill._name
    ctx.state["s09_power"] = list(ui.RectanglePower.powerline.yData)
    ctx.state["s09_freqs"] = list(ui.RectanglePower.powerline.xData)
    data, times = ui.PaintEventWidget.selected_data
    ctx.state["s09_selected_times"] = (float(times[0]), float(times[-1]))
    ctx.move_cursor(ctx.center(ui.RectanglePower.axes), 1.0)
    ctx.wait(1.5)

    ui.PaintEventWidget.reset()
    ctx.wait(0.3)
    ctx.caption(None)


def check(ctx):
    ui, state = ctx.ui, ctx.state
    assert state["s09_channel_shown"] == CHANNEL, (
        f"Periodogram panel shows '{state['s09_channel_shown']}', expected '{CHANNEL}'"
    )
    # The rectangle-row selection must have overridden Configuration > Periodogram's channel,
    # proving the panel is driven by the drawn rectangle, not the config combo.
    assert state["s09_channel_shown"] != state["s09_periodogram_channel_config"], (
        "Periodogram channel matches the Configuration combo default; "
        "the rectangle-row selection did not override it"
    )
    assert state["s09_freqs"] and state["s09_power"], "no periodogram data was computed"
    assert len(state["s09_freqs"]) == len(state["s09_power"])
    assert all(0.0 <= p <= 1.0 + 1e-9 for p in state["s09_power"]), "power is not scaled to 0-1"
    lo_t, hi_t = state["s09_selected_times"]
    assert lo_t < hi_t, "selected time window is empty"
    assert ui.events.count(SPINDLE_SLOT) == state["s09_count_before"], (
        "the selection rectangle was committed as an Event"
    )
    assert not ui.PaintEventWidget.stored_corners, "selection rectangle left on the paint overlay"
