def epoch_in_merged_event(borders, border_of_this_epoch):
    start, end = border_of_this_epoch
    result = []

    for interval in borders:
        if interval[1] <= start or interval[0] >= end:
            # No overlap, keep the interval as it is
            result.append(interval)
        elif interval[0] < start and interval[1] > end:
            # Interval completely contains the this_epoch, split it into two
            result.append([interval[0], start])
            result.append([end, interval[1]])
        elif interval[0] < start and interval[1] <= end:
            # Interval overlaps with the left side of this_epoch
            result.append([interval[0], start])
        elif interval[0] >= start and interval[1] > end:
            # Interval overlaps with the right side of this_epoch
            result.append([end, interval[1]])
        elif interval == border_of_this_epoch:
            result.append(interval)
    return result
