def enable_recording_ui(ui):
    """Turn on every menu and control that needs an open recording."""
    for menu in (ui.menu_stages, ui.menu_labels, ui.menu_detectors, ui.menu_filter,
                 ui.menu_utils, ui.menu_autoscore, ui.menu_config):
        menu.setEnabled(True)
    for control in (ui.toolbar_jump_to_epoch, ui.tool_nextunscored, ui.tool_nextuncertain,
                    ui.tool_nexttransition, ui.tool_nextevent, ui.tool_nexthuman):
        control.setEnabled(True)
    ui.HypnogramSlider.enable_slider()
