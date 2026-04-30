"""
YASA spindle detection wrapper.

Uses yasa.spindles_detect() to detect sleep spindles in EEG data.
Returns event time ranges (start_sec, end_sec) as list of [start, end] pairs.
"""

import numpy as np


def detect_spindles(signal_1d, sfreq, rel_pow=0.2, corr=0.65, rms=1.5,
                   min_dur=0.5, max_dur=2.0, freq_sp=(12, 15), freq_broad=(1, 30)):
    """
    Detect sleep spindles using YASA.

    Parameters
    ----------
    signal_1d : ndarray
        1D EEG signal (time samples).
    sfreq : float
        Sampling frequency in Hz.
    rel_pow : float, optional
        Minimum relative power threshold (default 0.2).
    corr : float, optional
        Minimum correlation threshold (default 0.65).
    rms : float, optional
        Minimum RMS threshold in standard deviations (default 1.5).
    min_dur : float, optional
        Minimum spindle duration in seconds (default 0.5).
    max_dur : float, optional
        Maximum spindle duration in seconds (default 2.0).
    freq_sp : tuple, optional
        Spindle frequency band (low, high) in Hz (default (12, 15)).
    freq_broad : tuple, optional
        Broad frequency band (low, high) in Hz for relative power (default (1, 30)).

    Returns
    -------
    list of [start, end]
        Detected spindle time ranges in seconds.
    """
    try:
        import yasa
    except ImportError:
        raise ImportError(
            "YASA is not installed. Install it with:\n"
            "  uv pip install yasa\n"
            "or\n"
            "  pip install yasa"
        )

    # Call YASA spindles_detect with thresh dictionary
    spindles = yasa.spindles_detect(
        signal_1d,
        sfreq,
        ch_names=["EEG"],
        freq_sp=freq_sp,
        freq_broad=freq_broad,
        duration=(min_dur, max_dur),
        thresh={
            "rel_pow": rel_pow,
            "corr": corr,
            "rms": rms,
        },
    )

    # SpindlesResults has a .summary() method that returns the DataFrame
    if spindles is None:
        return []

    events_sec = []

    try:
        # Get the summary DataFrame from SpindlesResults
        if hasattr(spindles, "summary"):
            df = spindles.summary()
        else:
            df = spindles

        if df is None or df.empty:
            return []

        # Extract Start and End times
        for _, row in df.iterrows():
            start = float(row["Start"])
            end = float(row["End"])
            events_sec.append([start, end])

    except Exception as e:
        import traceback
        print(f"[YASA] Error extracting spindles: {e}")
        traceback.print_exc()
        return []

    return events_sec
