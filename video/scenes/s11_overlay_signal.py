"""Scene 11: import an Overlay signal, move to several epochs, then remove the Overlay signal."""

import os

import numpy as np
from scipy import io, signal

FRACTIONS = [0.25, 0.4, 0.62, 0.8]  # where in the night to look at the overlay
LOWPASS_HZ = 12  # the overlay is a smoothed copy of the recording, so it differs visibly


def make_overlay_file(ctx):
    """EEGLAB .mat (EEG.data, EEG.srate, EEG.chanlocs.labels) off camera: the primary signals low-passed."""
    ui = ctx.ui
    srate = ui.config[0]["Sampling_rate_hz"]
    sos = signal.butter(4, LOWPASS_HZ, fs=srate, output="sos")
    data = signal.sosfiltfilt(sos, np.asarray(ui.eeg_data, dtype=np.float64), axis=1)
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
        ctx.click(ctx.spectrogram_point(epoch), duration=0.9)
        ctx.state["s11_epochs"].append((epoch, ctx.ui.this_epoch))
        ctx.wait(1.2)

    ctx.caption("Remove the Overlay signal again")
    ctx.click_menu("action_remove_overlay")
    ctx.wait(1.5)
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    assert os.path.exists(ctx.state["s11_path"]), "overlay file was not generated"
    assert ctx.state["s11_loaded"], "Overlay signal was not imported and shown"
    for epoch, displayed in ctx.state["s11_epochs"]:
        assert displayed == epoch, f"click on epoch {epoch} displayed epoch {displayed}"
    assert len({d for _, d in ctx.state["s11_epochs"]}) == len(FRACTIONS), "epochs did not change"
    assert getattr(ui, "eeg_data_ref", None) is None, "Overlay signal was not removed"
    assert not ui.show_overlay, "overlay is still shown"
