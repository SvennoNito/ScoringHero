from .event_epoch import event_epoch
from .draw_event_in_this_epoch import draw_event_in_this_epoch
from scoring.clean_epochs_to_uistages import clean_epochs_to_uiscoring
from scoring.write_scoring import write_scoring
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

    epoch_length = ui.config[0]["Epoch_length_s"]

    for container in ui.AnnotationContainer:
        new_borders = []
        for border in container.borders:
            segments = [list(border)]
            for e_start, e_end in erase_ranges:
                clipped = []
                for seg in segments:
                    if e_end <= seg[0] or e_start >= seg[1]:
                        clipped.append(seg)
                    else:
                        if seg[0] < e_start:
                            clipped.append([seg[0], e_start])
                        if seg[1] > e_end:
                            clipped.append([e_end, seg[1]])
                segments = clipped
            new_borders.extend(segments)

        container.borders = new_borders
        container.epochs = event_epoch(container.borders, epoch_length, ui.numepo)
        clean_epochs_to_uiscoring(ui, container)
        draw_event_in_this_epoch(ui, container)

    write_scoring(ui)
    ui.HypnogramWidget.update_hypnogram(ui)
    ui.HypnogramWidget.update_events(ui)
    ui.PaintEventWidget.reset()
