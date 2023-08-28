import numpy as np

def selected_channel(config, converted_corner, converted_shape):

    numchans_visible = len(
            [counter for counter, info in enumerate(config[1]) if info["Display_on_screen"]]
        )
    channel_anchors = np.array(
        [
            -config[0]["Distance_between_channels_muV"] * numchans_visible * chan_counter
            for chan_counter in range(numchans_visible)
        ]
    )
    rectangle_midpoint_in_amp = (
        min(converted_corner[1].y(), converted_corner[0].y()) + converted_shape[1] / 2
    )
    channel = np.argmin(abs(channel_anchors - rectangle_midpoint_in_amp))
    return channel