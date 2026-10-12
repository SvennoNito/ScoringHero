"""Scene 8: Configuration > Events tab shows the spindle slot's count under its default
label 'F1', then rename that slot to 'Spindle' on camera."""

from PySide6.QtCore import Qt

SPINDLE_SLOT = 1
OLD_LABEL = "F1"
NEW_LABEL = "Spindle"


def run(ctx):
    ui = ctx.ui
    ctx.wait_idle()
    ctx.state["s08_count_before"] = ui.events.count(SPINDLE_SLOT)

    ctx.caption("Configuration: Events tab")
    ctx.click_menu("action_config_window")
    window = ui.ConfigurationWindow
    window.move(ctx.to_global(ctx.at(ctx.window, 0.5, 0.5)) - window.rect().center())
    ctx.wait(0.6)

    tabs = window.tabs
    index = tabs.indexOf(ui.EventPage)
    ctx.click(ctx.window_point(tabs.tabBar(), tabs.tabBar().tabRect(index).center()), duration=0.7)
    if tabs.currentIndex() != index:
        tabs.setCurrentIndex(index)
    ctx.wait(0.6)

    labelbox = ui.EventPage.label[SPINDLE_SLOT]
    count_label = ui.EventPage.count_labels[SPINDLE_SLOT]
    assert labelbox.text() == OLD_LABEL, f"slot {SPINDLE_SLOT} is not labelled '{OLD_LABEL}'"
    assert count_label.text() == str(ui.events.count(SPINDLE_SLOT)), "count label does not match detected spindles"

    ctx.caption(f"{count_label.text()} spindles detected under the default label '{OLD_LABEL}'")
    ctx.click(labelbox, duration=0.7)
    window.activateWindow()  # the config dialog must be the active window for key events to reach it
    window.raise_()
    labelbox.setFocus()
    labelbox.selectAll()
    ctx.wait(0.6)

    ctx.caption(f"Rename '{OLD_LABEL}' to '{NEW_LABEL}'")
    ctx.type_text(labelbox, NEW_LABEL)
    ctx.wait(0.6)
    ctx.press_key(Qt.Key_Return, seconds=0.3)

    ctx.caption("Close the Configuration window")
    ctx.wait(1.5)
    window.close()
    ctx.wait(0.6)
    ctx.caption(None)


def check(ctx):
    ui, state = ctx.ui, ctx.state
    assert not ui.ConfigurationWindow.isVisible(), "Configuration window is still open"
    assert ui.events.label(SPINDLE_SLOT) == NEW_LABEL, "spindle slot was not renamed to 'Spindle'"
    assert ui.events.label(SPINDLE_SLOT) != OLD_LABEL
    assert ui.events.count(SPINDLE_SLOT) == state["s08_count_before"], "spindle count changed by the rename"
