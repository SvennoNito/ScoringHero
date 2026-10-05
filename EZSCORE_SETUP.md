# ezscore-f in ScoringHero

**ezscore-f** is a set of artifact-aware sleep stage classifiers for **two-channel
forehead EEG** (ZMax, DCM, CGX PatchEEG and comparable montages). Unlike the
other classifiers in ScoringHero it has a sixth class for **artifact**, so
epochs ruined by signal loss or movement no longer get a made-up sleep stage.

> Coon WG, Zerr P, Milsap G, Sikder N, Smith M, Dresler M, Reid M.
> *ezscore-f: A Set of Freely Available, Validated Sleep Stage Classifiers for
> Forehead EEG.* bioRxiv, 2025. [doi:10.1101/2025.06.02.657451](https://doi.org/10.1101/2025.06.02.657451)
> — source: <https://github.com/coonwg1/ezscore>

## Why a second Python environment is needed

`ezscore` pins **TensorFlow 2.15** and supports **Python 3.9–3.11 only**.
ScoringHero runs on Python ≥ 3.13, so ezscore cannot be installed alongside it.
ScoringHero therefore calls ezscore **out-of-process**, the same way it calls
SEED: the EEG is handed to `scoring/ezscore_worker.py`, which runs in a separate
interpreter and hands back the hypnogram and the class probabilities.

## One-time setup

From the ScoringHero folder:

```bash
python setup_ezscore.py
```

This creates `.venv_ezscore` (Python 3.11), installs `ezscore` into it, and
downloads the default `ez6` model. Options:

```bash
python setup_ezscore.py --model ez6rt   # download a different variant
python setup_ezscore.py --no-model      # environment only
```

Doing it by hand is equivalent:

```bash
uv venv .venv_ezscore --python 3.11
uv pip install --python .venv_ezscore ezscore
```

**On Windows that last command fails.** `ezscore` depends on `keras_nlp==0.9.3`,
which depends on `tensorflow-text`, which publishes no Windows wheels for any
version compatible with TensorFlow 2.15. Nothing in ezscore's inference path
imports `keras_nlp`, so install it without that dependency — this is what
`setup_ezscore.py` falls back to automatically:

```bash
uv pip install --python .venv_ezscore tensorflow==2.15 tf_keras "huggingface-hub>=0.33.1" \
    mne pandas numpy scikit-learn matplotlib seaborn lspopt
uv pip install --python .venv_ezscore --no-deps ezscore
```

ScoringHero finds `.venv_ezscore` automatically. Alternatives: set the
`EZSCORE_PYTHON` environment variable, or point the *Python executable* field in
the ezscore dialog at any interpreter that has ezscore installed. The choice is
remembered in `ezscore_settings.json`.

## Models

| Variant | Input | Size | Notes |
|---|---|---|---|
| `ez6` | median/IQR normalized | ~37 MB | Default. Best accuracy of the light models (81.3 %, κ = 0.74). |
| `ez6rt` | raw µV | ~37 MB | Real-time variant, no whole-night statistics needed (79.2 %, κ = 0.71). |
| `ez6moe` | median/IQR normalized | ~377 MB | Mixture of experts; can be more accurate but loads slowly. |

Weights are downloaded on first use into `~/.ezscore_models/<variant>` —
`ez6`/`ez6rt` from the ezscore GitHub repository, `ez6moe` from Hugging Face. If
you already cloned the ezscore repository, point the *Folder* field at its
`model` directory instead and nothing is downloaded.

## Standalone builds (.exe)

ezscore **cannot** be compiled into the ScoringHero binary: the build runs on
Python 3.13 and ezscore needs 3.9–3.11 plus TensorFlow 2.15. What the build does
carry is the small worker script, added as a data file in every build script:

```
--include-data-files=./scoring/ezscore_worker.py=scoring/ezscore_worker.py
```

Without that line the ezscore menu entry still appears but fails with
"ezscore_worker.py could not be found", listing the paths it checked. Nothing
else about the feature needs bundling — `widgets.ezscoreWindow` is already in the
`--include-module` list of each script.

Users of the .exe get the environment in one of three ways:

1. **In-app**: Autoscore → Forehead EEG Classifier (ezscore-f) →
   *Set up ezscore environment...*. This creates `.venv_ezscore` **next to the
   .exe** and installs ezscore, using the same code as `setup_ezscore.py`. It
   needs `uv` on the machine.
2. **Manually**: create `.venv_ezscore` next to the .exe with the commands above.
   It is detected automatically.
3. **Any interpreter**: set `EZSCORE_PYTHON`, or point the *Python executable*
   field at it. The choice is saved in `ezscore_settings.json`.

Model weights are never bundled either; they download to `~/.ezscore_models` on
first use.

Settings are stored next to the .exe (`ezscore_settings.json`), falling back to
`~/.scoringhero/` when that folder is read-only — never in the onefile
extraction directory, which is deleted when the app closes.

## Using it

**Autoscore → Forehead EEG Classifier (ezscore-f)** (`Ctrl+E`).

- **Channels** — pick the left and right forehead derivation. The signals are
  taken as displayed, so re-referencing, polarity flips and filters configured in
  the Configuration panel are applied first. ScoringHero converts them from µV to
  volts, which is what ezscore expects; ezscore resamples to 64 Hz and high-passes
  at 0.5 Hz itself.
- **Artifact epochs** — either left unscored (default) or scored as
  *Inconclusive*. Either way they are flagged as unclean and can additionally be
  marked with an event marker.
- **Output** — the per-epoch class probabilities (hypnodensity) can be stored in
  the scoring `.json` under `probabilities`, and ezscore's own summary figure
  (hypnodensity, hypnogram, dual spectrograms) can be shown when scoring finishes.

Scores are written with `source = "ezscore-f (<variant>)"` and the winning class
probability as `confidence`.

Hypnogram CSVs produced by `ezscore_demo.py` can also be imported directly via
**File → Load Scoring → Load ezscore-f Scoring (.csv)**, and ScoringHero can
export the same format via **File → Export as → ezscore-f (.csv)**.

## Troubleshooting

- **"No ezscore environment"** — `.venv_ezscore` is missing or the path is wrong.
  Run `python setup_ezscore.py`.
- **Download fails** — check the network, or clone
  <https://github.com/coonwg1/ezscore> and point the *Folder* field at its
  `model/ez6` directory.
- **Subprocess fails on import** — verify the environment:
  `.venv_ezscore\Scripts\python.exe -c "import ezscore, tensorflow"`.
- **Poor results on scalp PSG** — expected. ezscore-f was trained on forehead
  montages; use GSSC for standard scalp EEG/EOG.
