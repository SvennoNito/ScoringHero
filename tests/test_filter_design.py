"""
Tests for filter design: cutoff / notch frequency at the -3 dB point of the
displayed (zero-phase) signal.  Synthetic sinusoids go through apply_filter and
the amplitude ratio is measured.  No example data needed.
"""

import numpy as np
from filter.apply_filter import apply_filter, design_filter, zero_phase_gain
from config.channel_settings import default_channels

FS = 256.0
DURATION_S = 300.0
TOL_DB = 0.1


def _settings(**kw):
    return {**default_channels(1, ["C3"])[0], **kw}


def _gain_db(freq, settings, fs=FS):
    """Amplitude ratio (dB) of a sinusoid at freq after filtering, from the central half."""
    t = np.arange(int(fs * DURATION_S)) / fs
    x = np.sin(2 * np.pi * freq * t)
    y = apply_filter(x[None, :], fs, [settings])[0]
    seg = slice(len(t) // 4, 3 * len(t) // 4)
    basis = np.column_stack([np.sin(2 * np.pi * freq * t[seg]), np.cos(2 * np.pi * freq * t[seg])])
    coef, *_ = np.linalg.lstsq(basis, y[seg], rcond=None)
    return 20 * np.log10(np.hypot(*coef))


def test_highpass_cutoff_is_3db():
    for cutoff, order in [(0.3, 4), (1.0, 2), (5.0, 6), (0.5, 10)]:
        g = _gain_db(cutoff, _settings(Filter_hp_enabled=True, Filter_hp_cutoff=cutoff, Filter_hp_order=order))
        assert abs(g + 3.0) < TOL_DB, f"hp {cutoff} Hz order {order}: {g:.3f} dB"
    print("[OK] high-pass cutoff is -3 dB")


def test_lowpass_cutoff_is_3db():
    for cutoff, order in [(50.0, 4), (30.0, 2), (15.0, 8), (100.0, 6)]:
        g = _gain_db(cutoff, _settings(Filter_lp_enabled=True, Filter_lp_cutoff=cutoff, Filter_lp_order=order))
        assert abs(g + 3.0) < TOL_DB, f"lp {cutoff} Hz order {order}: {g:.3f} dB"
    print("[OK] low-pass cutoff is -3 dB")


def test_higher_order_is_steeper():
    """Order N+1 attenuates more than order N one octave into the stopband."""
    for n in (2, 3, 4):  # higher orders hit the cheby2 stopband floor (2x60 dB zero-phase)
        hp = [_gain_db(1.0, _settings(Filter_hp_enabled=True, Filter_hp_cutoff=2.0, Filter_hp_order=o))
              for o in (n, n + 1)]
        assert hp[1] < hp[0], f"hp order {n}->{n + 1}: {hp}"
        lp = [_gain_db(40.0, _settings(Filter_lp_enabled=True, Filter_lp_cutoff=20.0, Filter_lp_order=o))
              for o in (n, n + 1)]
        assert lp[1] < lp[0], f"lp order {n}->{n + 1}: {lp}"
    print("[OK] higher order attenuates more, cutoff unchanged")


def test_notch_deepest_at_notch_and_3db_at_1hz():
    for notch, order in [(50.0, 4), (60.0, 2)]:
        s = _settings(Filter_notch_enabled=True, Filter_notch_cutoff=notch, Filter_notch_order=order)
        for f in (notch - 1.0, notch + 1.0):
            g = _gain_db(f, s)
            assert abs(g + 3.0) < 0.3, f"notch {notch} order {order} at {f}: {g:.3f} dB"
        centre = _gain_db(notch, s)
        for d in (0.5, 1.0, 2.0):  # inside the equiripple stopband the response wiggles around its floor
            for f in (notch - d, notch + d):
                assert centre < _gain_db(f, s), f"notch {notch}: not deepest vs {f} Hz"
        assert centre < -20.0, f"notch {notch}: only {centre:.1f} dB at the notch frequency"
    print("[OK] notch deepest at notch frequency, -3 dB at +-1 Hz")


def test_invalid_cutoff_leaves_signal_unchanged():
    rng = np.random.default_rng(0)
    x = rng.standard_normal((1, 4096))
    nyq = FS / 2
    cases = [
        {"Filter_hp_enabled": True, "Filter_hp_cutoff": 0.0},
        {"Filter_hp_enabled": True, "Filter_hp_cutoff": nyq},
        {"Filter_lp_enabled": True, "Filter_lp_cutoff": 0.0},
        {"Filter_lp_enabled": True, "Filter_lp_cutoff": nyq},
        {"Filter_lp_enabled": True, "Filter_lp_cutoff": nyq + 20},
        {"Filter_notch_enabled": True, "Filter_notch_cutoff": 0.5},
        {"Filter_notch_enabled": True, "Filter_notch_cutoff": nyq - 0.5},
    ]
    for kw in cases:
        y = apply_filter(x, FS, [_settings(**kw)])
        assert np.array_equal(x, y), f"signal changed for {kw}"
    print("[OK] invalid cutoff leaves signal unchanged")


def test_design_matches_applied_response():
    """The response shown in the filter window (zero_phase_gain of design_filter) is the applied one."""
    s = _settings(Filter_lp_enabled=True, Filter_lp_cutoff=30.0, Filter_lp_order=5)
    sos = design_filter("lp", 30.0, 5, FS)
    for f in (10.0, 30.0, 45.0):
        measured = _gain_db(f, s)
        predicted = 20 * np.log10(zero_phase_gain(sos, f, FS)[0])
        assert abs(measured - predicted) < 0.05, f"{f} Hz: measured {measured:.3f} vs design {predicted:.3f}"
    assert design_filter("lp", 0.0, 4, FS) is None
    assert design_filter("hp", FS / 2, 4, FS) is None
    print("[OK] design response matches applied filter")


if __name__ == "__main__":
    test_highpass_cutoff_is_3db()
    test_lowpass_cutoff_is_3db()
    test_higher_order_is_steeper()
    test_notch_deepest_at_notch_and_3db_at_1hz()
    test_invalid_cutoff_leaves_signal_unchanged()
    test_design_matches_applied_response()
