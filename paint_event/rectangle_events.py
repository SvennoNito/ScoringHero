"""Event edits made with the mouse and the event hotkeys. Widget coordinates become seconds
here; Events and the main window's GUI step (`edit_events`) only see plain seconds."""

from .convert_to_seconds import convert_to_seconds
from .order_by_time import order_by_time


def event_hotkey(slot, ui):
    """Event slot hotkey: add the drawn rectangles (clipped to the displayed range) to the
    slot, or toggle the whole current epoch if none is drawn."""
    corners, _ = convert_to_seconds(ui, ui.PaintEventWidget.stored_corners)
    if not corners:
        ui.edit_events(lambda events: events.toggle_epoch(slot, int(ui.this_epoch)))
    else:
        times = ui.times[int(ui.this_epoch)][0]
        spans = [(max(c[0].x(), times[0]), min(c[1].x(), times[-1])) for c in corners]
        ui.edit_events(lambda events: events.add(slot, spans))
    _reset_rectangles(ui)


def erase_events_in_rectangles(ui):
    """Erase the events under the drawn rectangles in every slot."""
    if not ui.PaintEventWidget.stored_corners:
        return
    for corners in ui.PaintEventWidget.stored_corners:
        order_by_time(corners)
    converted, _ = convert_to_seconds(ui, ui.PaintEventWidget.stored_corners)
    ranges = [(c[0].x(), c[1].x()) for c in converted]
    ui.edit_events(lambda events: events.erase(ranges))
    _reset_rectangles(ui)


def drop_or_relabel(ui, time):
    """Click without a rectangle: with an event key held, move the smallest event under the
    click to that slot; otherwise drop every event under it."""
    held_key = getattr(ui, "held_event_key", None)
    if held_key is not None and ui.edit_events(lambda events: events.relabel(time, held_key)):
        ui.relabeled_event = True
    else:
        ui.edit_events(lambda events: events.drop(time))


def _reset_rectangles(ui):
    ui.PaintEventWidget.reset()
    ui.SignalWidget.text_period.setText("")
    ui.SignalWidget.text_amplitude_signal.setText("")
    ui.SignalWidget.text_amplitude_box.setText("")
