def order_corners(corner):
    if corner[0].x() > corner[1].x():
        tmp = corner[0].x()
        corner[0].setX(corner[1].x())
        corner[1].setX(tmp)    