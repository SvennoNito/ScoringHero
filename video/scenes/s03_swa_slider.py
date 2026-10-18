"""Scene 3: drag the SWA slider to show SWA moments, then click the Hypnogram to jump in time."""

from PySide6.QtCore import QPoint, QPointF
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


def _hypnogram_point(ctx, hour, fy=0.5):
    """Window position of `hour` into the night in the Hypnogram Panel (fy: fraction of the stage range)."""
    axes = ctx.ref("HypnogramWidget.axes")
    view = axes.getViewBox()
    y_lo, y_hi = view.viewRange()[1]
    scene = view.mapViewToScene(QPointF(hour, y_lo + (1 - fy) * (y_hi - y_lo)))
    return axes.viewport().mapTo(ctx.window, axes.mapFromScene(scene))


def run(ctx):
    ctx.caption("Drag the SWA slider to smooth the slow-wave activity curve of the Hypnogram")
    slider = ctx.ref("HypnogramSlider.slider")
    ctx.state["s03_values"] = []
    for dy in (0.9, -0.5, 0.3):  # fractions of the slider height: down, back up, down a bit
        _drag_handle_by(ctx, slider, round(dy * slider.height()))
        ctx.state["s03_values"].append(slider.value())
        ctx.wait(0.8)

    ctx.caption("The Hypnogram navigates the night too: click it to jump to that time")
    ctx.click(_hypnogram_point(ctx, 4.5), duration=1.0)
    ctx.wait(1.5)


def check(ctx):
    values = ctx.state["s03_values"]
    assert len(set(values)) > 1, f"the SWA slider did not move: {values}"
    assert ctx.ui.HypnogramWidget.kernel == ctx.ui.HypnogramSlider.slider.value(), "slider did not smooth the SWA curve"
    assert ctx.ui.this_epoch == 540, f"displayed Epoch {ctx.ui.this_epoch}, expected Epoch 540 (4.5h into the night)"
