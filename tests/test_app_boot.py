"""Smoke: the app boots headless and loads a recording; also proves the `loaded_ui` fixture."""


def test_example_recording_loads(loaded_ui):
    assert loaded_ui.eeg_data.shape[0] == len(loaded_ui.config[1])
    assert len(loaded_ui.stages) > 0
