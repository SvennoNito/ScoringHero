"""Scene 11: import an Overlay signal, move to several epochs, then remove the Overlay signal."""

import os

import numpy as np
from scipy import io

FRACTIONS = [0.25, 0.4, 0.62, 0.8]  # where in the night to look at the overlay
DRIFT_HZ = 0.3  # the overlay is the recording plus mild noise and a slow drift


def make_overlay_file(ctx):
    """EEGLAB .mat (EEG.data, EEG.srate, EEG.chanlocs.labels) off camera: the primary signals plus mild noise and 0.3 Hz drift."""
    ui = ctx.ui
    srate = ui.config[0]["Sampling_rate_hz"]
    rng = np.random.default_rng(0)
    data = np.asarray(ui.eeg_data, dtype=np.float64)
    seconds = np.arange(data.shape[1]) / srate
    noise = rng.normal(0, 0.1 * data.std(axis=1, keepdims=True), data.shape)
    drift = 0.5 * data.std(axis=1, keepdims=True) * np.sin(2 * np.pi * DRIFT_HZ * seconds)
    data = data + noise + drift
    chanlocs = np.array([(name,) for name in ui.signal_names], dtype=[("labels", "O")]).reshape(1, -1)
    path = os.path.join(ctx.video_dir, "overlay_signal.mat")
    io.savemat(path, {"EEG": {"data": data, "srate": float(srate), "chanlocs": chanlocs}})
    return path


def run(ctx):
    ctx.state["s11_path"] = path = make_overlay_file(ctx)
    ctx.caption("Import an Overlay signal: a second Recording drawn over the Displayed signal")
    with ctx.file_dialogs(open=path):
        ctx.click_menu("action_import_overlay_eeglab")
    ctx.wait_until(lambda: getattr(ctx.ui, "eeg_data_ref", None) is not None)
    ctx.state["s11_loaded"] = ctx.ui.eeg_data_ref is not None and ctx.ui.show_overlay
    ctx.wait(1.5)

    ctx.caption("Move to several Epochs to compare the two signals")
    spectrogram = ctx.ref("SpectogramWidget.graphics")
    ctx.move_cursor(ctx.center(spectrogram), 0.8)
    ctx.state["s11_epochs"] = []
    for fraction in FRACTIONS:
        epoch = int(fraction * ctx.ui.numepo)
        ctx.click_epoch(epoch)
        ctx.state["s11_epochs"].append(epoch)
        ctx.wait(1.2)

    ctx.caption("Remove the Overlay signal again")
    ctx.click_menu("action_remove_overlay")
    ctx.wait(1.5)
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    assert os.path.exists(ctx.state["s11_path"]), "overlay file was not generated"
    assert ctx.state["s11_loaded"], "Overlay signal was not imported and shown"
    assert len(set(ctx.state["s11_epochs"])) == len(FRACTIONS), "not every click ran or the Epoch did not change"
    assert getattr(ui, "eeg_data_ref", None) is None, "Overlay signal was not removed"
    assert not ui.show_overlay, "overlay is still shown"
