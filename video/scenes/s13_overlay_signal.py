"""Scene 13: import an Overlay signal (visible file dialog: example_data_overlay.mat), hold on the current Epoch to show it drawn over the Displayed signal, then remove it."""

import os

import numpy as np
from scipy import io

GAIN = 1.4  # the overlay is the recording itself, amplified, plus a tiny slow drift: it must not hide the primary signal
DRIFT_HZ = 0.3
DRIFT_FRACTION = 0.05  # of each channel's standard deviation


def make_overlay_file(ctx):
    """EEGLAB .mat (EEG.data, EEG.srate, EEG.chanlocs.labels) off camera: the primary signals x1.4 plus a tiny 0.3 Hz drift."""
    ui = ctx.ui
    srate = ui.config[0]["Sampling_rate_hz"]
    data = np.asarray(ui.eeg_data, dtype=np.float64)
    seconds = np.arange(data.shape[1]) / srate
    drift = DRIFT_FRACTION * data.std(axis=1, keepdims=True) * np.sin(2 * np.pi * DRIFT_HZ * seconds)
    data = GAIN * data + drift
    chanlocs = np.array([(name,) for name in ui.signal_names], dtype=[("labels", "O")]).reshape(1, -1)
    path = os.path.join(ctx.directory, "example_data_overlay.mat")
    io.savemat(path, {"EEG": {"data": data, "srate": float(srate), "chanlocs": chanlocs}})
    return path


def run(ctx):
    ctx.state["s13_path"] = path = make_overlay_file(ctx)
    ctx.caption("Import an Overlay signal: a second Recording drawn over the Displayed signal")
    with ctx.file_dialogs(open=(ctx.directory, "example_data_overlay.mat", "*.mat")):
        ctx.click_menu("action_import_overlay_eeglab")
    ctx.wait_until(lambda: getattr(ctx.ui, "eeg_data_ref", None) is not None)
    ctx.state["s13_loaded"] = ctx.ui.eeg_data_ref is not None and ctx.ui.show_overlay
    ctx.wait(2.5)

    ctx.caption("Remove the Overlay signal again")
    ctx.click_menu("action_remove_overlay")
    ctx.wait(1.5)
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    assert os.path.exists(ctx.state["s13_path"]), "overlay file was not generated"
    assert ctx.state["s13_loaded"], "Overlay signal was not imported and shown"
    assert getattr(ui, "eeg_data_ref", None) is None, "Overlay signal was not removed"
    assert not ui.show_overlay, "overlay is still shown"
