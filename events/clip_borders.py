def clip_borders(borders, erase_ranges):
    """Return borders with all given time ranges clipped out.

    Parameters
    ----------
    borders : list of [start, end]
    erase_ranges : list of (start, end) tuples

    Returns
    -------
    list of [start, end] with the erased regions removed.
    """
    new_borders = []
    for border in borders:
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
    return new_borders
