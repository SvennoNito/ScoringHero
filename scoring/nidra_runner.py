"""
nidra_runner.py — ONNX inference for the NIDRA ezscore-f models.

The preprocessing, windowing and label remapping below are a faithful port of
NIDRA 0.2.3 (`NIDRA/forehead_scorer.py`, MIT licence, Paul Zerr,
https://github.com/paulzerr/nidra). Porting rather than importing keeps
ScoringHero free of NIDRA's GUI dependency chain (Flask, pywebview,
pydantic-core) — only `onnxruntime` and `mne` are needed. Any change to
upstream's preprocessing has to be mirrored here.

`run_forehead` returns:

    stages : int array (n_epochs,)
        0=Wake 1=N1 2=N2 3=N3 5=REM 6=Artifact — NIDRA's own code scheme
        (4 stays unused, where AASM once had N4).
    probs : float array (n_epochs, 6)
        Columns [Wake, N1, N2, N3, REM, Artifact].
"""

import numpy as np

# Class order of the probability matrix returned below
FOREHEAD_CLASSES = ["Wake", "N1", "N2", "N3", "REM", "Artifact"]

# NIDRA stage code -> column of the probability matrix
CODE_TO_COLUMN = {0: 0, 1: 1, 2: 2, 3: 3, 5: 4, 6: 5}

EPOCH_SECONDS = 30
FOREHEAD_SAMPLE_RATE = 64   # ezscore-f operating rate
FOREHEAD_SEQUENCE = 100     # epochs per sequence fed to the RNN


class NidraCancelled(Exception):
    """Raised when the user aborts a running NIDRA job."""


def _report(tick, message):
    """Forward a progress message; a tick returning False cancels the run."""
    if tick is not None and tick(message) is False:
        raise NidraCancelled()


def _open_session(model_path):
    import onnxruntime as ort

    # The published graphs use a deprecated upsample attribute, which makes
    # onnxruntime print a warning per layer on every session — silence both the
    # global and the per-session logger.
    ort.set_default_logger_severity(3)
    options = ort.SessionOptions()
    options.log_severity_level = 3
    return ort.InferenceSession(
        model_path, sess_options=options, providers=["CPUExecutionProvider"]
    )


# --------------------------------------------------------------------------
# Forehead EEG — ez6 / ez6moe
# --------------------------------------------------------------------------

def run_forehead(data_volts, sfreq, model_path, tick=None):
    """Score a two-channel forehead montage with ez6 or ez6moe.

    `data_volts` is a (2, n_samples) array in volts — the same convention the
    ezscore-f path uses. The signal is resampled to 64 Hz, high-pass filtered
    at 0.5 Hz and median/IQR normalized before inference.
    """
    import mne

    data = np.asarray(data_volts, dtype=np.float64)
    if data.ndim != 2 or data.shape[0] != 2:
        raise ValueError(f"Expected a (2, n_samples) array, got {data.shape}.")

    _report(tick, "Preprocessing (resample to 64 Hz, high-pass 0.5 Hz) ...")

    mne.set_log_level("ERROR")
    info = mne.create_info(
        ch_names=["eegl", "eegr"], sfreq=float(sfreq), ch_types=["eeg", "eeg"]
    )
    raw = mne.io.RawArray(data, info, verbose=False)
    raw.resample(sfreq=FOREHEAD_SAMPLE_RATE, verbose=False)
    raw.filter(l_freq=0.5, h_freq=None, verbose=False)

    signal = raw.get_data()
    for index in range(signal.shape[0]):
        channel = signal[index]
        mad = np.median(np.abs(channel - np.median(channel)))
        if mad == 0:
            mad = 1
        normalized = (channel - np.median(channel)) / mad
        iqr = np.subtract(*np.percentile(normalized, [75, 25]))
        signal[index] = np.clip(normalized, -20 * iqr, 20 * iqr)

    sequences, n_full_sequences, n_epochs = _forehead_sequences(signal)

    _report(tick, "Loading model ...")
    session = _open_session(model_path)
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    _report(tick, f"Running inference on {n_epochs} epochs ...")

    last_sequence = sequences[-1]
    valid_in_last = int(np.sum(~np.isnan(last_sequence.sum(axis=(1, 2)))))

    if valid_in_last == FOREHEAD_SEQUENCE:
        raw_predictions = session.run(
            [output_name], {input_name: sequences.astype(np.float32)}
        )[0].reshape(-1, 6)
    else:
        # The padded tail must not be fed to the RNN: its NaNs would smear over
        # the real epochs during the backward pass
        head = session.run(
            [output_name], {input_name: sequences[:n_full_sequences].astype(np.float32)}
        )[0].reshape(-1, 6) if n_full_sequences else np.empty((0, 6), dtype=np.float32)
        tail = session.run(
            [output_name],
            {input_name: last_sequence[:valid_in_last][None, ...].astype(np.float32)},
        )[0].reshape(-1, 6)
        raw_predictions = np.concatenate([head, tail], axis=0)

    predictions = raw_predictions[:n_epochs, :]

    # Model output order -> [Wake, N1, N2, N3, REM, Artifact]
    probs = predictions[:, [4, 2, 1, 0, 3, 5]]
    stages = probs.argmax(axis=1).astype(int)
    stages[stages == 5] = 6  # artifact
    stages[stages == 4] = 5  # REM

    return stages, probs.astype(float)


def _forehead_sequences(signal):
    """Epoch a (2, n_samples) signal into (n_sequences, 100, 1920, 2), NaN-padded."""
    samples_per_epoch = EPOCH_SECONDS * FOREHEAD_SAMPLE_RATE
    n_channels = signal.shape[0]
    n_epochs = int(np.floor(signal.shape[1] / samples_per_epoch))
    if n_epochs < 1:
        raise ValueError(
            f"The recording is shorter than one {EPOCH_SECONDS} s epoch."
        )

    epoched = np.full((n_channels, n_epochs, samples_per_epoch), np.nan)
    for channel in range(n_channels):
        for index in range(n_epochs):
            start = index * samples_per_epoch
            epoched[channel, index, :] = signal[channel, start:start + samples_per_epoch]

    n_full_sequences, remainder = divmod(n_epochs, FOREHEAD_SEQUENCE)
    n_sequences = n_full_sequences + (1 if remainder else 0)

    sequences = np.full(
        (n_sequences, FOREHEAD_SEQUENCE, samples_per_epoch, n_channels),
        np.nan,
        dtype=np.float32,
    )
    for index in range(n_full_sequences):
        start = index * FOREHEAD_SEQUENCE
        sequences[index] = np.transpose(
            epoched[:, start:start + FOREHEAD_SEQUENCE, :], (1, 2, 0)
        )
    if remainder:
        start = n_full_sequences * FOREHEAD_SEQUENCE
        sequences[n_full_sequences, :remainder] = np.transpose(
            epoched[:, start:, :], (1, 2, 0)
        )

    return sequences, n_full_sequences, n_epochs


# --------------------------------------------------------------------------
# Summary figure
# --------------------------------------------------------------------------

# Same stage colours the hypnogram widget uses, so the figure reads like the
# rest of the application
_STAGE_COLORS = {
    "Wake":     "#e8c547",
    "N1":       "#de4968",
    "N2":       "#8c6bb1",
    "N3":       "#3b6ea5",
    "REM":      "#41b6a6",
    "Artifact": "#888888",
}


def render_summary_figure(stages, probs, class_names, path, title="NIDRA"):
    """Write a hypnodensity + hypnogram summary PNG for a scored recording."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    hours = np.arange(len(stages)) * EPOCH_SECONDS / 3600.0

    figure, axes = plt.subplots(
        2, 1, figsize=(12, 6), sharex=True
    )

    # Hypnodensity — stacked class probabilities
    bottom = np.zeros(len(stages))
    for column, name in enumerate(class_names):
        values = probs[:, column]
        axes[0].fill_between(
            hours, bottom, bottom + values,
            color=_STAGE_COLORS.get(name, "#999999"), linewidth=0, label=name,
        )
        bottom = bottom + values
    axes[0].set_ylim(0, 1)
    axes[0].set_xlim(hours[0], hours[-1] + EPOCH_SECONDS / 3600.0)
    axes[0].set_ylabel("Class probability")
    axes[0].set_title(f"{title} — hypnodensity and hypnogram")

    # Hypnogram — plotted on the conventional Wake/REM/N1/N2/N3 ladder
    levels = {"Wake": 0, "REM": -1, "N1": -2, "N2": -3, "N3": -4}
    code_to_name = {0: "Wake", 1: "N1", 2: "N2", 3: "N3", 5: "REM", 6: "Artifact"}

    ladder = np.array(
        [levels.get(code_to_name.get(int(code)), np.nan) for code in stages],
        dtype=float,
    )
    axes[1].step(hours, ladder, where="post", color="#333333", linewidth=1.0)

    artifacts = np.flatnonzero(np.asarray(stages) == 6)
    for index in artifacts:
        axes[1].axvspan(
            hours[index],
            hours[index] + EPOCH_SECONDS / 3600.0,
            color=_STAGE_COLORS["Artifact"], alpha=0.35, linewidth=0,
        )
    axes[1].set_yticks([0, -1, -2, -3, -4])
    axes[1].set_yticklabels(["W", "REM", "N1", "N2", "N3"])
    axes[1].set_ylim(-4.5, 0.5)
    axes[1].set_xlabel("Time (hours)")
    axes[1].set_ylabel("Sleep stage")

    # One legend for both panels, below the figure so it never covers the data
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(
        handles, labels,
        loc="lower center", bbox_to_anchor=(0.5, -0.04),
        ncol=len(class_names), fontsize=9, frameon=False,
    )

    figure.tight_layout()
    figure.savefig(path, format="png", dpi=130, bbox_inches="tight")
    plt.close(figure)

    return path
