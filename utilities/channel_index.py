def rebuild_channel_index(ui):
    """Build cached channel name to index mapping from config.

    Creates a dictionary mapping channel names to their indices in ui.config[1].
    This cache avoids repeated linear searches through channel_names when looking up
    a channel's index during navigation (e.g., in TF widget, periodogram, spectrogram).

    Called after config load and when channel settings change.
    """
    ui.channel_name_to_idx = {ch["Channel_name"]: i for i, ch in enumerate(ui.config[1])}
