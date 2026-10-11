"""Scene 12: tour through all tabs of the Configuration, change only cosmetic items (colormaps), close."""
import copy

COSMETIC_KEYS = ("Spectrogram_colormap", "Wavelet_colormap")


def _tab_point(ctx, tabs, index):
    bar = tabs.tabBar()
    return bar.mapToGlobal(bar.tabRect(index).center()) - ctx._origin()


def _choose_colormap(ctx, box):
    """Open the drop-down, show it, then pick the next colormap in the list."""
    ctx.click(box, duration=0.8)
    ctx.wait(0.6)
    box.hidePopup()
    box.setCurrentIndex(1)
    ctx.wait(0.8)


def run(ctx):
    ui = ctx.ui
    ctx.state["s12_config_before"] = copy.deepcopy(ui.config[0])
    ctx.state["s12_stages_before"] = list(ui.scoring.stages())
    ctx.caption("Configuration: a tour through every tab")
    ctx.click_menu("action_config_window")
    window = ui.ConfigurationWindow
    window.move(ctx.to_global(ctx.at(ctx.window, 0.5, 0.5)) - window.rect().center())
    ctx.wait(0.8)

    tabs = window.tabs
    for index in range(tabs.count()):
        ctx.click(_tab_point(ctx, tabs, index), duration=0.7)
        if tabs.currentIndex() != index:
            tabs.setCurrentIndex(index)
        if tabs.widget(index) is ui.SpectrogramPage:
            ctx.caption("Spectrogram tab: change the colormap (cosmetic only)")
            _choose_colormap(ctx, ui.SpectrogramPage.optionboxes["Spectrogram_colormap"][0])
        elif tabs.widget(index) is ui.WaveletPage:
            ctx.caption("Wavelet tab: change the colormap (cosmetic only)")
            _choose_colormap(ctx, ui.WaveletPage.optionboxes["Wavelet_colormap"][0])
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
    before, after = ctx.state["s12_config_before"], ui.config[0]
    assert not ui.ConfigurationWindow.isVisible(), "Configuration window is still open"
    for key in COSMETIC_KEYS:
        assert after[key] != before[key], f"{key} was not changed"
    others = {k for k in before if before[k] != after[k]}
    assert others == set(COSMETIC_KEYS), f"scoring-relevant settings changed: {others - set(COSMETIC_KEYS)}"
    assert list(ui.scoring.stages()) == ctx.state["s12_stages_before"], "scoring changed"
