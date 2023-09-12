def selected_samples(times, this_epoch, converted_corner):
    time_index = (converted_corner[0].x() <= times[this_epoch][0]) & (
        times[this_epoch][0] <= converted_corner[1].x()
    )
    return times[this_epoch][1][time_index], times[this_epoch][0][time_index]
