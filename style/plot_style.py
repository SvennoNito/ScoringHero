MUTED = "#6b7280"


def soften_axes(plot, color=MUTED):
    """Muted axis lines and tick text so the data, not the chrome, carries the contrast."""
    for name in ("left", "bottom"):
        axis = plot.getAxis(name)
        axis.setPen(color)
        axis.setTextPen(color)
