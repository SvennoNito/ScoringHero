from .clip_borders import clip_borders
from .event_deletion import rebuild_event_epochs, refresh_after_event_deletion
from paint_event.convert_to_seconds import convert_to_seconds
from paint_event.order_by_time import order_by_time


def erase_events_in_rectangles(ui):
    if not ui.PaintEventWidget.stored_corners:
        return

    for corners in ui.PaintEventWidget.stored_corners:
        order_by_time(corners)

    converted_corners, _ = convert_to_seconds(ui, ui.PaintEventWidget.stored_corners)

    erase_ranges = [
        (corners[0].x(), corners[1].x())
        for corners in converted_corners
        if corners[1].x() > corners[0].x()
    ]

    if not erase_ranges:
        ui.PaintEventWidget.reset()
        return

    for container in ui.AnnotationContainer:
        container.borders = clip_borders(container.borders, erase_ranges)
        rebuild_event_epochs(ui, container)

    # Also redraws the events and clears the erase rectangles
    refresh_after_event_deletion(ui)
