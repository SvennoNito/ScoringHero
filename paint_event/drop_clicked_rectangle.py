from annotations.drop_event import drop_event

def drop_clicked_rectangle(ui, converted_corners, rectangle_sizes):
    if (rectangle_sizes[-1][0] < 0.1 or rectangle_sizes[-1][1] < 0.1):
        for index, corners in enumerate(ui.PaintEventWidget.stored_corners[:-1]):
            if (
                min(corners[0].x(), corners[1].x()) < ui.PaintEventWidget.stored_corners[-1][0].x() < max(corners[0].x(), corners[1].x())
                and min(corners[0].y(), corners[1].y()) < ui.PaintEventWidget.stored_corners[-1][0].y() < max(corners[0].y(), corners[1].y())
            ):

                # Drop clicked on rectancle
                ui.PaintEventWidget.stored_corners.pop(index)
                rectangle_sizes.pop(index)
                converted_corners.pop(index)
        
        # Also drop events
        drop_event(ui, converted_corners[-1])

        # Drop zero size rectangle
        ui.PaintEventWidget.stored_corners.pop(-1)
        rectangle_sizes.pop(-1)
        converted_corners.pop(-1)



    return ui.PaintEventWidget.stored_corners, converted_corners, rectangle_sizes
