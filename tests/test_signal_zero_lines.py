"""Zero lines: one per visible channel on the EEG panel, at that channel's real
baseline (its vertical shift minus its channel offset)."""

import pyqtgraph as pg

from eeg.displayed_signal import settings_changed


def _visible_chans(ui):
    return [c for c in ui.config[1] if c["Display_on_screen"]]


def _zero_positions(ui):
    return [line.value() for line in ui.SignalWidget.drawn_zerolines]


def test_each_visible_channel_has_its_own_zero_line_at_its_baseline_in_muv_mode(loaded_ui):
    ui = loaded_ui
    chans = _visible_chans(ui)
    numchans = len(chans)
    assert len(ui.SignalWidget.drawn_zerolines) == numchans

    expected = [
        chan["Vertical_shift"] - ui.config[0]["Distance_between_channels_muV"] * numchans * i
        for i, chan in enumerate(chans)
    ]
    assert _zero_positions(ui) == expected


def test_zero_line_moves_by_the_same_amount_as_the_signal_when_vertical_shift_changes(loaded_ui):
    ui = loaded_ui
    before = _zero_positions(ui)[0]

    ui.config[1][0]["Vertical_shift"] = before + 50
    settings_changed(ui)

    after = _zero_positions(ui)[0]
    assert after - before == 50


def test_z_standardize_not_stacked_gives_every_visible_channel_its_own_zero_line(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Robust_z_standardize"] = True
    ui.config[0]["Stack_channels"] = False
    settings_changed(ui)

    chans = _visible_chans(ui)
    numchans = len(chans)
    assert len(ui.SignalWidget.drawn_zerolines) == numchans
    assert numchans > 1  # otherwise "not only the top channel" is untestable

    expected = [chan["Vertical_shift"] - 8 * i for i, chan in enumerate(chans)]
    assert _zero_positions(ui) == expected
    # Not only the top channel: every position differs from the next.
    assert len(set(_zero_positions(ui))) == numchans


def test_stacked_mode_puts_all_zero_lines_at_the_shared_baseline(loaded_ui):
    ui = loaded_ui
    ui.config[0]["Stack_channels"] = True
    settings_changed(ui)

    chans = _visible_chans(ui)
    expected = [chan["Vertical_shift"] for chan in chans]
    assert _zero_positions(ui) == expected


def test_grid_draws_no_horizontal_lines_but_keeps_the_1s_vertical_ticks(loaded_ui):
    ui = loaded_ui
    grid_items = [
        item for item in ui.SignalWidget.axes.plotItem.items if isinstance(item, pg.GridItem)
    ]
    assert len(grid_items) == 1
    grid_item = grid_items[0]
    assert grid_item.opts["tickSpacing"][0] == [1]  # x: unchanged 1 s ticks
    assert grid_item.opts["tickSpacing"][1] == []  # y: no horizontal lines


def test_amplitude_lines_are_unaffected_by_zero_lines(loaded_ui):
    ui = loaded_ui
    numchans = len(_visible_chans(ui))
    other_horizontal_lines = [
        item
        for item in ui.SignalWidget.axes.plotItem.items
        if isinstance(item, pg.InfiniteLine)
        and item.angle == 0
        and item not in ui.SignalWidget.drawn_zerolines
    ]
    assert len(other_horizontal_lines) == 2 * numchans
