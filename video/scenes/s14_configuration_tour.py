"""Scene 14: tour through all tabs of the Configuration, change only cosmetic items (colormaps
and the Channels-tab colour of a few channels), close."""
import copy

COSMETIC_KEYS = ("Spectrogram_colormap", "Wavelet_colormap")
BLACK_CHANNEL_COLOR = "Black"
ORANGE_CHANNEL_COLOR = "Orange"
ORANGE_CHANNELS = ("O1-A2", "O2-A1")


def _choose_colormap(ctx, box):
    """Open the drop-down, show it, then pick the next colormap in the list."""
    ctx.click(box, duration=0.8)
    ctx.wait(0.6)
    box.hidePopup()
    box.setCurrentIndex(1)
    ctx.wait(0.8)


def _choose_channel_color(ctx, box, color_name):
    """Open the drop-down, show it, then pick a specific colour by name."""
    ctx.click(box, duration=0.6)
    ctx.wait(0.4)
    box.hidePopup()
    box.setCurrentIndex(box.findText(color_name))
    ctx.wait(0.4)


def run(ctx):
    ui = ctx.ui
    ctx.wait_idle()
    ctx.state["s14_config_before"] = copy.deepcopy(ui.config[0])
    ctx.state["s14_stages_before"] = list(ui.scoring.stages())
    ctx.caption("Configuration: a tour through every tab")
    ctx.click_menu("action_config_window")
    window = ui.ConfigurationWindow
    window.move(ctx.to_global(ctx.at(ctx.window, 0.5, 0.5)) - window.rect().center())
    ctx.wait(0.8)

    tabs = window.tabs
    for index in range(tabs.count()):
        ctx.click(ctx.window_point(tabs.tabBar(), tabs.tabBar().tabRect(index).center()), duration=0.7)
        if tabs.currentIndex() != index:
            tabs.setCurrentIndex(index)
        if tabs.widget(index) is ui.SpectrogramPage:
            ctx.caption("Spectrogram tab: change the colormap (cosmetic only)")
            _choose_colormap(ctx, ui.SpectrogramPage.optionboxes["Spectrogram_colormap"][0])
        elif tabs.widget(index) is ui.WaveletPage:
            ctx.caption("Wavelet tab: change the colormap (cosmetic only)")
            _choose_colormap(ctx, ui.WaveletPage.optionboxes["Wavelet_colormap"][0])
        elif tabs.widget(index) is ui.ChannelPage:
            ctx.caption("Channels tab: set a few channel colours (cosmetic only)")
            channel_page = ui.ChannelPage
            names = [c["Channel_name"] for c in ui.config[1]]
            _choose_channel_color(ctx, channel_page.color[0], BLACK_CHANNEL_COLOR)
            for name in ORANGE_CHANNELS:
                _choose_channel_color(ctx, channel_page.color[names.index(name)], ORANGE_CHANNEL_COLOR)
        else:
            ctx.wait(1.2)

    ctx.caption("Apply the cosmetic change and close; scoring is untouched")
    ctx.click(window.apply_button, duration=0.8)
    ctx.wait(0.8)
    window.close()
    ctx.wait(0.8)
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    before, after = ctx.state["s14_config_before"], ui.config[0]
    assert not ui.ConfigurationWindow.isVisible(), "Configuration window is still open"
    for key in COSMETIC_KEYS:
        assert after[key] != before[key], f"{key} was not changed"
    others = {k for k in before if before[k] != after[k]}
    assert others == set(COSMETIC_KEYS), f"scoring-relevant settings changed: {others - set(COSMETIC_KEYS)}"
    assert list(ui.scoring.stages()) == ctx.state["s14_stages_before"], "scoring changed"

    channels = {c["Channel_name"]: c for c in ui.config[1]}
    assert channels[ui.config[1][0]["Channel_name"]]["Channel_color"] == BLACK_CHANNEL_COLOR, \
        "first channel's colour was not set to Black"
    for name in ORANGE_CHANNELS:
        assert channels[name]["Channel_color"] == ORANGE_CHANNEL_COLOR, f"{name}'s colour was not set to Orange"
