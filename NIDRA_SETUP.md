# NIDRA (ezscore-f) in ScoringHero

**NIDRA** is a sleep-scoring package that ships validated classifiers as
**ONNX** models. ScoringHero uses its **ezscore-f** models (`ez6`, `ez6moe`) for
two-channel forehead EEG and runs them directly, in its own interpreter.

> Zerr P. *NIDRA: super simple sleep scoring.* 2025.
> <https://github.com/paulzerr/nidra> — manual: <https://nidra.netlify.app/>
>
> ezscore-f: Coon et al., bioRxiv 2025,
> [doi:10.1101/2025.06.02.657451](https://doi.org/10.1101/2025.06.02.657451).

## Setup

No second Python environment is needed. The ONNX models need only two optional
packages:

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
ScoringHero's Python. `autoscoring/nidra_runner.py` is instead a port of NIDRA's
preprocessing and inference (MIT licence). It is verified to reproduce NIDRA
0.2.3 exactly — identical hypnograms and class probabilities to float32
precision for `ez6` and `ez6moe`. **If NIDRA changes its preprocessing, that
port has to be updated with it.**

## Models

| Model | Recording | File | Size |
|---|---|---|---|
| `ez6` | two-channel forehead EEG | `ez6.onnx` | ~12 MB |
| `ez6moe` | two-channel forehead EEG | `ez6moe.onnx` | ~117 MB |

Weights are downloaded on first use from
<https://huggingface.co/pzerr/NIDRA_models> into `~/.nidra_models`. Before
downloading, ScoringHero looks in NIDRA's own model directory
(`%LOCALAPPDATA%\NIDRA\models` on Windows, `~/Library/Application Support/NIDRA/models`
on macOS, `~/.local/share/NIDRA/models` on Linux), so if you already run NIDRA
nothing is downloaded twice. The *Folder* field in the dialog overrides both.

## Using it

**Autoscore → NIDRA (ezscore-f)** (`Ctrl+N`).

- **Forehead channels** — pick the left and right derivation. The right one can
  be left as *none*, which duplicates the left channel.
- **Model** — `ez6` or `ez6moe`.
- Signals are taken **as displayed**, so re-referencing, polarity flips and
  filters from the Configuration panel are applied first. ScoringHero hands the
  models volts and they normalize the input themselves (median/IQR).
- **Artifact epochs** — the sixth class. Those epochs are left unscored
  (default) or scored *Inconclusive*, are flagged as unclean, and can be marked
  with an event marker.
- **Output** — the per-epoch class probabilities (hypnodensity) can be stored in
  the scoring `.json` under `probabilities`, and a summary figure
  (hypnodensity + hypnogram) can be shown when scoring finishes.

Scores are written with `source = "NIDRA (<model>)"` and the winning class
probability as `confidence`.

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

## Troubleshooting

- **"NIDRA requirements missing"** — run `uv sync --extra nidra`.
- **Download fails** — fetch the `.onnx` files by hand from
  <https://huggingface.co/pzerr/NIDRA_models> and point the *Folder* field at
  the directory holding them.
- **Poor results on scalp EEG** — expected; the models are trained on forehead
  montages.
