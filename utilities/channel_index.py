def rebuild_visible_channels(ui):
    """Build cached list of visible channel indices.

    Stores the indices of channels with Display_on_screen=True in ui.visible_channel_idx.
    This cache avoids repeated filtering of config[1] during navigation and rendering.
    """
    ui.visible_channel_idx = [
        i for i, ch in enumerate(ui.config[1]) if ch["Display_on_screen"]
    ]
