"""Channel-name pills on the signal, spectrogram and time-frequency panels."""

import pytest
from PySide6.QtWidgets import QApplication

from utilities.redraw_gui import redraw_gui

LONG_NAME = "Left_frontal_electrode_" * 5 + "-A2"


def _show_wide(ui):
    """Give the panels a realistic width (a hidden window leaves them tiny)."""
    window = ui.SignalWidget.axes.window()
    window.resize(1500, 900)
    window.show()
    QApplication.processEvents()


def _limit(view):
    return 0.25 * view.viewport().width()


def test_signal_pills_show_short_names_whole_without_tooltip(loaded_ui):
    _show_wide(loaded_ui)
    pills = loaded_ui.SignalWidget.written_channel_labels
    names = [c["Channel_name"] for c in loaded_ui.config[1] if c["Display_on_screen"]]
    assert [p.text() for p in pills] == names
    assert all(p.toolTip() == "" for p in pills)


def test_long_signal_channel_name_is_elided_in_the_middle_with_full_name_tooltip(loaded_ui):
    ui = loaded_ui
    _show_wide(ui)
    first_shown = next(c for c in ui.config[1] if c["Display_on_screen"])
    first_shown["Channel_name"] = LONG_NAME
    redraw_gui(ui)

    pill = ui.SignalWidget.written_channel_labels[0]
    assert "…" in pill.text()
    assert pill.text().startswith("Left_frontal") and pill.text().endswith("-A2")
    assert pill.boundingRect().width() <= _limit(ui.SignalWidget.axes)
    assert pill.toolTip() == LONG_NAME


@pytest.mark.parametrize("panel, view, set_name", [
    ("SpectogramWidget", lambda ui: ui.SpectogramWidget.graphics, "Channel_for_spectogram"),
    ("TFWidget", lambda ui: ui.TFWidget.graphics, "Wavelet_channel"),
])
def test_analysis_panels_use_the_same_pill(loaded_ui, panel, view, set_name):
    ui = loaded_ui
    _show_wide(ui)
    pill = getattr(ui, panel).channel_pill
    ui.config[0][set_name] = LONG_NAME
    if panel == "SpectogramWidget":
        ui.SpectogramWidget.draw_spectogram(ui.power, ui.freqs, ui.freqsOI, ui.config)
    else:
        from utilities.tf_config_helper import call_tf_widget

        call_tf_widget(ui)

    assert "…" in pill.text() and pill.text().endswith("-A2")
    assert pill.boundingRect().width() <= _limit(view(ui))
    assert pill.toolTip() == LONG_NAME
