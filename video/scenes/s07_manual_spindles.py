"""Scene 7: add a missed spindle by drawing a rectangle, delete a false-positive spindle with a click.

Uses ctx.state from scene 5 ("spindles", "spindle_epochs"). Both choices are data-driven, on C3-A2:
    missed spindle   NREM Epoch without a detection whose 11-16 Hz (sigma) burst is the strongest
                     relative to its broadband signal; the rectangle covers 1 s around the burst
    false positive   detected spindle (outside the missed one's Epoch) with the weakest sigma burst
Their Epochs (1-based, as displayed) are printed in the run output.
"""

import numpy as np
from PySide6.QtCore import QPoint, QPointF, Qt
from scenes.s05_spindle_detection import SPINDLE_SLOT as SLOT
from scipy.signal import butter, filtfilt

CHANNEL = "C3-A2"
SIGMA_HZ = (11.0, 16.0)
NREM = ("N2", "N3")
RECT_S = 1.0
HOTKEY = Qt.Key(Qt.Key_F1 + SLOT - 1)  # Event hotkeys F1, F2, ... belong to slots 1, 2, ...


def _sigma(ui):
    """(signal, sigma-band signal, srate) of the channel, whole night."""
    srate = ui.config[0]["Sampling_rate_hz"]
    signal = np.asarray(ui.eeg_data[ui.signal_names.index(CHANNEL)], dtype=float)
    b, a = butter(4, SIGMA_HZ, btype="bandpass", fs=srate)
    return signal, filtfilt(b, a, signal), srate


def _ratio(signal, sigma, lo, hi):
    """Sigma RMS over broadband RMS of the samples [lo, hi)."""
    return np.sqrt(np.mean(sigma[lo:hi] ** 2)) / (np.sqrt(np.mean(signal[lo:hi] ** 2)) + 1e-12)


def choose(ui, spans, spindle_epochs):
    """(missed_start_s, missed_end_s, missed_epoch, false_positive_index, false_positive_epoch)."""
    signal, sigma, srate = _sigma(ui)
    length = ui.config[0]["Epoch_length_s"]
    stages = ui.scoring.stages()
    taken = {e for covered in spindle_epochs for e in covered}
    best = None
    for epoch in range(ui.numepo):
        if epoch in taken or stages[epoch] not in NREM:
            continue
        # keep a margin to the epoch edges, so the rectangle stays inside the Epoch
        lo, hi = int((epoch * length + 2) * srate), int(((epoch + 1) * length - 2) * srate)
        score = _ratio(signal, sigma, lo, hi)
        if best is None or score > best[0]:
            best = (score, epoch, lo, hi)
    if best is None:
        raise RuntimeError("no NREM Epoch without a spindle detection")
    _, epoch, lo, hi = best
    envelope = np.convolve(np.abs(sigma[lo:hi]), np.ones(int(RECT_S * srate)) / int(RECT_S * srate), mode="same")
    margin = int(RECT_S * srate / 2)
    centre = lo + margin + int(np.argmax(envelope[margin:len(envelope) - margin]))
    start = (centre - margin) / srate
    missed = (start, start + RECT_S, epoch)

    candidates = [i for i, covered in enumerate(spindle_epochs) if epoch not in covered]
    weakest = min(candidates, key=lambda i: _ratio(signal, sigma, int(spans[i][0] * srate), int(spans[i][1] * srate)))
    middle = (spans[weakest][0] + spans[weakest][1]) / 2
    return (*missed, weakest, min(int(middle // length), ui.numepo - 1))


def _signal_x(ctx, seconds):
    """Window x of a time in the displayed Epoch."""
    paint = ctx.ref("PaintEventWidget")
    scene = ctx.ref("SignalWidget.axes").plotItem.vb.mapViewToScene(QPointF(seconds, 0))
    return paint.mapTo(ctx.window, paint.rect().topLeft()).x() + round(scene.x())


def _paint_y(ctx, fraction):
    paint = ctx.ref("PaintEventWidget")
    return paint.mapTo(ctx.window, paint.rect().topLeft()).y() + round(paint.height() * fraction)


def _install_key_filter(ctx):
    """The Event hotkeys live in the app-wide key filter that scoringhero.main() installs; the headless boot has none."""
    if "key_filter" not in ctx.state:
        import scoringhero as sh

        ctx.state["key_filter"] = sh.GlobalKeyFilter(ctx.ui, ctx.app)
        ctx.app.installEventFilter(ctx.state["key_filter"])


def run(ctx):
    ui = ctx.ui
    _install_key_filter(ctx)
    ctx.wait_idle()
    spans = ctx.state["spindles"]
    start, end, epoch, false_index, false_epoch = choose(ui, spans, ctx.state["spindle_epochs"])
    false_span = spans[false_index]
    ctx.state.update(s07_missed_epoch=epoch, s07_false_epoch=false_epoch, s07_before=ui.events.count(SLOT))
    print(f"s07: missed spindle added in Epoch {epoch + 1} ({start:.2f}-{end:.2f} s); "
          f"false positive deleted in Epoch {false_epoch + 1} ({false_span[0]:.2f}-{false_span[1]:.2f} s)", flush=True)

    ctx.caption(f"A spindle was missed: go to Epoch {epoch + 1}")
    ctx.click_epoch(epoch, duration=1.0)
    ctx.wait(1.0)

    ctx.caption("Draw a rectangle around it, then press the Event hotkey")
    y0, y1 = _paint_y(ctx, 0.35), _paint_y(ctx, 0.75)  # below the paint overlay's length label
    ctx.drag(QPoint(_signal_x(ctx, start), y0), QPoint(_signal_x(ctx, end), y1), duration=1.0)
    assert ui.PaintEventWidget.stored_corners, "the rectangle was not drawn"
    ctx.wait(0.8)
    ctx.press_key(HOTKEY, seconds=1.0)
    ctx.state["s07_after_add"] = ui.events.count(SLOT)
    ctx.wait(1.5)

    ctx.caption(f"A false positive: go to Epoch {false_epoch + 1}")
    ctx.click_epoch(false_epoch, duration=1.0)
    ctx.wait(1.0)

    ctx.caption("Click on the spindle to delete it")
    middle = (false_span[0] + false_span[1]) / 2
    ctx.click(QPoint(_signal_x(ctx, middle), _paint_y(ctx, 0.5)), duration=1.0)
    ctx.state["s07_after_delete"] = ui.events.count(SLOT)
    ctx.wait(1.5)
    ctx.caption(None)


def check(ctx):
    state = ctx.state
    assert state["s07_after_add"] == state["s07_before"] + 1, \
        f"event count after add: {state['s07_after_add']}, expected {state['s07_before'] + 1}"
    assert state["s07_after_delete"] == state["s07_after_add"] - 1, \
        f"event count after delete: {state['s07_after_delete']}, expected {state['s07_after_add'] - 1}"
    assert not ctx.ui.PaintEventWidget.stored_corners, "rectangles are left on the paint overlay"
