"""Menu bar structure and enabled state, observed through the booted app."""

from PySide6.QtGui import QKeySequence

MENU_ORDER = [
    "File", "Stages", "Events", "Autoscore", "Detectors", "Filter",
    "Utilities", "Compare", "Configuration", "Help",
]


def _menus(ui):
    return {a.text(): a.menu() for a in ui.menu.actions()}


def _items(menu):
    return [a.text() for a in menu.actions() if not a.isSeparator()]


def test_menu_bar_order(loaded_ui):
    assert [a.text() for a in loaded_ui.menu.actions()] == MENU_ORDER


def test_detectors_filter_and_utilities_contents(loaded_ui):
    menus = _menus(loaded_ui)
    assert _items(menus["Detectors"]) == [
        "K-Complex Detection (MT-KCD)",
        "Spindle Detection (MT-Spindle)",
    ]
    assert _items(menus["Filter"]) == ["Open filter settings"]
    assert _items(menus["Utilities"]) == ["Zoom on selected EEG"]


def test_detectors_and_filter_menus_wait_for_a_recording(unloaded_ui, loaded_ui):
    before = _menus(unloaded_ui)
    after = _menus(loaded_ui)
    for name in ("Detectors", "Filter", "Utilities"):
        assert not before[name].isEnabled(), name
        assert after[name].isEnabled(), name


def test_ctrl_f_opens_filter_settings(loaded_ui):
    action = _menus(loaded_ui)["Filter"].actions()[0]
    assert action.shortcut() == QKeySequence("Ctrl+F")
    action.trigger()
    assert loaded_ui.FilterWindow.isVisible()
    loaded_ui.FilterWindow.close()
