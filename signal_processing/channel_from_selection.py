import numpy as np


def channel_from_selection(config, converted_corner, converted_shape, ui=None):
    # Use cached visible channel indices if available
    if ui and hasattr(ui, 'visible_channel_idx'):
        visible_indices = ui.visible_channel_idx
    else:
        visible_indices = [counter for counter, info in enumerate(config[1]) if info["Display_on_screen"]]

    numchans_visible = len(visible_indices)
    channel_anchors = np.array(
        [
            config[1][visible_indices[chan_counter]]["Vertical_shift"] - config[0]["Distance_between_channels_muV"] * numchans_visible * chan_counter
            for chan_counter in range(numchans_visible)
        ]
    )
    rectangle_midpoint_in_amp = (
        min(converted_corner[1].y(), converted_corner[0].y()) + converted_shape[1] / 2
    )
    displayed_channel = np.argmin(abs(channel_anchors - rectangle_midpoint_in_amp))
    channel = visible_indices[displayed_channel]

    return displayed_channel, channel
