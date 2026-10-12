"""Scene 4: drag the SWA slider to show SWA moments, then jump to the Epoch with the most SWA."""

import numpy as np
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QStyle, QStyleOptionSlider


def _handle_centre(ctx, slider):
    """Window position of the slider handle."""
    option = QStyleOptionSlider()
    slider.initStyleOption(option)
    rect = slider.style().subControlRect(QStyle.CC_Slider, option, QStyle.SC_SliderHandle, slider)
    return ctx.window_point(slider, rect.center())


def _drag_handle_by(ctx, slider, dy):
    """Grab the handle and drag it `dy` pixels down (negative: up), staying inside the slider."""
    start = _handle_centre(ctx, slider)
    top, bottom = ctx.at(slider, 0, 0).y() + 2, ctx.at(slider, 0, 1).y() - 2
    ctx.drag(start, QPoint(start.x(), max(top, min(bottom, start.y() + dy))), duration=1.4)


def run(ctx):
    ctx.caption("Drag the SWA slider to smooth the slow-wave activity curve of the Hypnogram")
    slider = ctx.ref("HypnogramSlider.slider")
    widget = ctx.ref("HypnogramWidget")
    ctx.state["s04_values"] = []
    for dy in (0.9, -0.5, 0.3):  # fractions of the slider height: down, back up, down a bit
        _drag_handle_by(ctx, slider, round(dy * slider.height()))
        ctx.state["s04_values"].append(slider.value())
        ctx.wait(0.8)

    # the heaviest-SWA Epoch is the peak of the curve the slider has just drawn
    curve = np.asarray(widget.swa_item.getData()[1], dtype=float)
    heaviest = int(np.nanargmax(curve))
    ctx.state["s04_heaviest"] = heaviest
    ctx.caption(f"Jump to the Epoch with the most SWA (Epoch {heaviest + 1})")
    readout = ctx.ref("StatusReadout.epoch")
    ctx.click(readout.label, duration=1.0)
    ctx.wait(0.4)
    for digit in str(heaviest + 1):
        ctx.press_key(getattr(Qt, f"Key_{digit}"), seconds=0.25)
    ctx.press_key(Qt.Key_Return, seconds=0.2)
    ctx.wait(1.5)


def check(ctx):
    values = ctx.state["s04_values"]
    assert len(set(values)) > 1, f"the SWA slider did not move: {values}"
    assert ctx.ui.HypnogramWidget.kernel == ctx.ui.HypnogramSlider.slider.value(), "slider did not smooth the SWA curve"
    assert ctx.ui.this_epoch == ctx.state["s04_heaviest"], (
        f"displayed Epoch {ctx.ui.this_epoch}, expected the heaviest SWA Epoch {ctx.state['s04_heaviest']}"
    )
