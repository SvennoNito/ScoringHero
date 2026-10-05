# NIDRA in ScoringHero

**NIDRA** is a sleep-scoring package that ships two validated classifier
families as **ONNX** models: **U-Sleep 2.0** for full polysomnography and the
**ezscore-f** models (`ez6`, `ez6moe`) for two-channel forehead EEG. ScoringHero
runs those models directly, in its own interpreter.

> Zerr P. *NIDRA: super simple sleep scoring.* 2025.
> <https://github.com/paulzerr/nidra> — manual: <https://nidra.netlify.app/>
>
> U-Sleep: Perslev et al., *npj Digital Medicine* 4:72 (2021); the weights NIDRA
> ships were re-trained by Rossi et al. for
> [SLEEPYLAND](https://github.com/biomedical-signal-processing/sleepyland).
> ezscore-f: Coon et al., bioRxiv 2025,
> [doi:10.1101/2025.06.02.657451](https://doi.org/10.1101/2025.06.02.657451).

## Setup

No second Python environment is needed — unlike the ezscore-f menu entry, which
needs TensorFlow 2.15 on Python 3.9–3.11 (see [EZSCORE_SETUP.md](EZSCORE_SETUP.md)).
The ONNX models need only two optional packages:

```bash
uv sync --extra nidra          # onnxruntime + mne
```

or, in any environment:

```bash
pip install onnxruntime mne
```

Without them the menu entry still appears and explains what is missing.

The `nidra` package itself is deliberately **not** a dependency: it would pull
in Flask, pywebview and a pinned `pydantic-core` that has no wheel for
ScoringHero's Python. `scoring/nidra_runner.py` is instead a port of NIDRA's
preprocessing and inference (MIT licence). It is verified to reproduce NIDRA
0.2.3 exactly — identical hypnograms and class probabilities to float32
precision for `ez6`, `ez6moe` and both U-Sleep graphs. **If NIDRA changes its
preprocessing, that port has to be updated with it.**

## Models

| Model | Recording | File | Size |
|---|---|---|---|
| `u-sleep-nsrr-2024` | scalp PSG, EEG + EOG | `u-sleep-nsrr-2024.onnx` | ~12 MB |
| `u-sleep-nsrr-2024` | scalp PSG, EEG only | `u-sleep-nsrr-2024_eeg.onnx` | ~12 MB |
| `ez6` | two-channel forehead EEG | `ez6.onnx` | ~12 MB |
| `ez6moe` | two-channel forehead EEG | `ez6moe.onnx` | ~117 MB |

Weights are downloaded on first use from
<https://huggingface.co/pzerr/NIDRA_models> into `~/.nidra_models`. Before
downloading, ScoringHero looks in NIDRA's own model directory
(`%LOCALAPPDATA%\NIDRA\models` on Windows, `~/Library/Application Support/NIDRA/models`
on macOS, `~/.local/share/NIDRA/models` on Linux), so if you already run NIDRA
nothing is downloaded twice. The *Folder* field in the dialog overrides both.

## Using it

**Autoscore → NIDRA (U-Sleep 2.0 / ezscore-f)** (`Ctrl+N`).

- **Recording type** — *Full PSG* selects U-Sleep, *Wearable* the forehead
  models. The channel selection and the available models follow from it.
- **PSG channels** — pick the **EEG** channels and, optionally, the **EOG**
  channels. Every EEG × EOG combination is scored separately and the class
  probabilities are averaged; this ensembling is what makes U-Sleep robust, and
  it costs runtime in proportion to the number of combinations. Without an EOG
  channel the EEG-only graph is used and each EEG channel forms its own group.
- **Forehead channels** — pick the left and right derivation, as for ezscore-f.
- Signals are taken **as displayed**, so re-referencing, polarity flips and
  filters from the Configuration panel are applied first. ScoringHero hands the
  models volts; U-Sleep's robust scaling makes the unit irrelevant there, the
  forehead models normalize the same way ezscore does.
- **Artifact epochs** — only the forehead models have an artifact class. Those
  epochs are left unscored (default) or scored *Inconclusive*, are flagged as
  unclean, and can be marked with an event marker. U-Sleep always assigns one
  of the five sleep stages.
- **Output** — the per-epoch class probabilities (hypnodensity) can be stored in
  the scoring `.json` under `probabilities`, and a summary figure
  (hypnodensity + hypnogram) can be shown when scoring finishes.

Scores are written with `source = "NIDRA (<model>)"` and the winning class
probability as `confidence`.

## Which entry should I use?

| | Use |
|---|---|
| Scalp PSG | **NIDRA / U-Sleep 2.0**, or GSSC (`Ctrl+G`) |
| Forehead EEG, ez6 or ez6moe | **NIDRA** — no TensorFlow environment needed |
| Forehead EEG, `ez6rt` (real-time variant) | ezscore-f (`Ctrl+E`) — NIDRA ships no ONNX export of it |
| Forehead EEG, ezscore's own summary figure | ezscore-f (`Ctrl+E`) |

`ez6` and `ez6moe` produce the same numbers through either entry point.

## Standalone builds (.exe)

`onnxruntime` and `mne` are bundled by the build scripts that sync the extra
(`build-win-gssc.bat`, `build-win-gssc-dev.bat`), via

```
--include-package=onnxruntime ^
--include-package-data=onnxruntime ^
```

Model weights are never bundled; they download to `~/.nidra_models` on first
use. Builds that do not carry onnxruntime still start and show the menu entry —
it then reports the missing packages instead of scoring.

## Note on hypnogram CSVs

NIDRA writes hypnogram CSVs with `0=Wake 1=N1 2=N2 3=N3 5=REM 6=Artifact`, which
is **not** the scheme of the ezscore-f CSVs ScoringHero imports via
*File → Load Scoring → Load ezscore-f Scoring (.csv)* (`1=N1 … 5=Wake`). Loading
a NIDRA CSV through that importer would silently mislabel Wake and REM — score
inside ScoringHero, or convert the codes first.

## Troubleshooting

- **"NIDRA requirements missing"** — run `uv sync --extra nidra`.
- **Download fails** — fetch the `.onnx` files by hand from
  <https://huggingface.co/pzerr/NIDRA_models> and point the *Folder* field at
  the directory holding them.
- **Poor results on forehead EEG with U-Sleep** (or on scalp EEG with `ez6`) —
  expected; the models are trained on different montages.
- **Scoring takes long** — each EEG × EOG combination is a separate pass over
  the night. Fewer channels, or no EOG, is proportionally faster.
