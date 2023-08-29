import numpy as np
def merge_borders(borders):
    merged_borders = []

    for border in sorted(borders, key=lambda x: x[0]):
        if not merged_borders or border[0] >= merged_borders[-1][1]:
            merged_borders.append([border[0], border[1]])   
        else:
            merged_borders[-1][1] = max(merged_borders[-1][1], border[1])  
    return np.array(merged_borders)