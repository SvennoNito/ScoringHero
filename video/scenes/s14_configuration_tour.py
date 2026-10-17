"""Scene 14: tour through the Configuration (Events, Spectrogram and Periodogram tabs are skipped): on the
Channels tab set a few channel colours, stack then unstack the channels, flip one channel and drag another
to a new row; on the Wavelet tab change the colormap; apply, close."""
import copy

from PySide6.QtCore import QModelIndex, QPoint
from PySide6.QtWidgets import QLabel

COSMETIC_KEYS = ("Wavelet_colormap",)
SKIPPED_TABS = ("Events", "Spectrogram", "Periodogram")
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


def _grip(ctx, page, row):
    """Window position of the drag handle of channel list `row`."""
    item = page.channel_list.item(row)
    grip = next(label for label in page.channel_list.itemWidget(item).findChildren(QLabel) if label.text() == "⠿")
    return ctx.center(grip)


def _drag_last_visible_row_to_top(ctx, page):
    """Drag the lowest fully visible channel row to the top of the list; returns its channel name.
    The glide is filmed with real mouse events, but the offscreen platform has no drag-and-drop (QDrag.exec
    returns at once), so the drop itself is made on the list's model, which fires the same rowsMoved
    signal a real drop does."""
    view = page.channel_list
    view.scrollToTop()
    ctx.wait(0.2)
    viewport = view.viewport().rect()
    rows = [r for r in range(view.count()) if viewport.contains(view.visualItemRect(view.item(r)))]
    source = rows[-1]
    name = page.channel_config[source]["Channel_name"]
    first_row = view.visualItemRect(view.item(0))
    start = _grip(ctx, page, source)
    ctx.drag(start, ctx.window_point(view.viewport(), QPoint(first_row.left() + 40, first_row.top() + 2)), duration=1.2)
    view.model().moveRows(QModelIndex(), source, 1, QModelIndex(), 0)
    ctx.wait(0.3)
    return name


def run(ctx):
    ui = ctx.ui
    ctx.wait_idle()
    ctx.state["s14_config_before"] = copy.deepcopy(ui.config[0])
    ctx.state["s14_stages_before"] = list(ui.scoring.stages())
    names = [c["Channel_name"] for c in ui.config[1]]
    ctx.state["s14_first_channel"] = names[0]
    ctx.caption("Configuration: a tour through the tabs")
    ctx.click_menu("action_config_window")
    window = ui.ConfigurationWindow
    window.move(ctx.to_global(ctx.at(ctx.window, 0.5, 0.5)) - window.rect().center())
    ctx.wait(0.8)

    tabs = window.tabs
    for index in range(tabs.count()):
        if tabs.tabText(index) in SKIPPED_TABS:
            continue
        ctx.click(ctx.window_point(tabs.tabBar(), tabs.tabBar().tabRect(index).center()), duration=0.7)
        if tabs.currentIndex() != index:
            tabs.setCurrentIndex(index)
        if tabs.widget(index) is ui.WaveletPage:
            ctx.caption("Wavelet tab: change the colormap (cosmetic only)")
            _choose_colormap(ctx, ui.WaveletPage.optionboxes["Wavelet_colormap"][0])
        elif tabs.widget(index) is ui.ChannelPage:
            page = ui.ChannelPage
            ctx.caption("Channels tab: set a few channel colours (cosmetic only)")
            _choose_channel_color(ctx, page.color[0], BLACK_CHANNEL_COLOR)
            for name in ORANGE_CHANNELS:
                _choose_channel_color(ctx, page.color[names.index(name)], ORANGE_CHANNEL_COLOR)

            ctx.wait_idle()
            ctx.caption("Stack the channels on top of each other ...")
            stack_box = page.stack_channels_checkbox
            indicator = ctx.window_point(stack_box, QPoint(10, stack_box.height() // 2))  # the box is wider than its label
            ctx.click(indicator)
            ctx.state["s14_stacked"] = ui.config[0].get("Stack_channels")
            ctx.wait(2.0)
            ctx.caption("... and unstack them again")
            ctx.wait_idle()
            ctx.click(indicator)
            ctx.wait(1.2)

            ctx.wait_idle()
            ctx.caption("Flip the polarity of one channel")
            ctx.click(page.flip[0])
            ctx.wait(1.2)

            ctx.wait_idle()
            ctx.caption("Drag a channel to a different position")
            ctx.state["s14_moved_channel"] = _drag_last_visible_row_to_top(ctx, page)
            ctx.wait(1.2)
        else:
            ctx.wait(1.2)

    ctx.caption("Apply the changes and close; scoring is untouched")
    ctx.wait_idle()  # the busy indicator swallows mouse input while a flip/reorder is being rebuilt
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
    assert ctx.state["s14_stacked"], "channels were not stacked"
    assert not after.get("Stack_channels"), "channels are still stacked"
    assert list(ui.scoring.stages()) == ctx.state["s14_stages_before"], "scoring changed"

    channels = {c["Channel_name"]: c for c in ui.config[1]}
    first = ctx.state["s14_first_channel"]
    assert channels[first]["Channel_color"] == BLACK_CHANNEL_COLOR, "first channel's colour was not set to Black"
    assert channels[first]["Flip_polarity"], "first channel was not flipped"
    for name in ORANGE_CHANNELS:
        assert channels[name]["Channel_color"] == ORANGE_CHANNEL_COLOR, f"{name}'s colour was not set to Orange"
    moved = ctx.state["s14_moved_channel"]
    assert ui.config[1][0]["Channel_name"] == moved and moved != first, "a channel was not dragged to the top"
