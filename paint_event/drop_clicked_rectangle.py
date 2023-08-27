def drop_clicked_rectangle(stored_corners, rectangle_sizes):
    if rectangle_sizes[-1][0] == 0:
        for index, corners in enumerate(stored_corners[:-1]):
            if (
                corners[0].x() < stored_corners[-1][0].x() < corners[1].x() and
                corners[0].y() < stored_corners[-1][0].y() < corners[1].y()
                ):
                stored_corners.pop(index)
                rectangle_sizes.pop(index)
        stored_corners.pop(-1)
        rectangle_sizes.pop(-1)   

    return stored_corners, rectangle_sizes     