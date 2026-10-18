# Walk-through video

Renders a silent, captioned 1920x1080, 30 fps walk-through of ScoringHero by driving the real main window with Qt input events (issue #55).

```
uv run --extra gssc python video/make_video.py            # -> video/scoringhero_walkthrough.mp4
uv run --extra gssc python video/make_video.py --cut presentation   # -> video/scoringhero_presentation.mp4
uv run --extra gssc python video/make_video.py --smoke    # 640x360, 6 fps, state asserted after each scene
uv run --extra gssc python video/make_video.py --scenes s01 s02   # only these scenes (inside the chosen cut)
```

- Cuts (`CUTS` in `video/scenes/__init__.py`): `walkthrough` (default) = every scene; `presentation` = every scene except 12 (Jump buttons) and 14 (Overlay signal), defined by exclusion so new scenes join it automatically. `--cut NAME` writes `video/scoringhero_NAME.mp4` (`_nocaptions` with `--no-captions`); an unknown cut exits with the list of cuts.
- `--extra gssc` is required: scene 5 runs the GSSC Autoscorer for real.
- Scenes run in film order (`video/scenes/__init__.py`); the film opens on the empty window and scene 1 loads the example recording through File > Load EEG with the cursor on the menus, via a real, non-native file dialog filmed at a temp folder named "... ScoringHero example" — the cursor clicks `example_data.mat`, then Open. Later scenes depend on earlier ones (scene 8 needs the spindles of scene 6, scene 11 derives its Comparison scoring from the Primary scoring after scene 9), so `--scenes` subsets only work for independent scenes.
- Scene 2 jumps the spectrogram to four landmark Epochs (first N1, first N2, first N3, 10th REM, in the second REM period) computed at render time from the example recording's tracked reference scoring (`example_data.json`, never loaded into the app itself), then jumps back to Epoch 1 via the Epoch counter and stages the first ten Epochs Wake by hand through the Stage menu and the Wake hotkey.
- Runs on a temp copy of `example_data`; tracked files are never changed.
- The smoke run is manual (needs GSSC, takes a few minutes); it is not part of pytest or the commit hook.
- Generated files in `video/` (`.mp4`, `.json`, `.mat`, `.pdf`) are gitignored.
- Scene 11 imports a Comparison scoring through a real, filmed file dialog (`example_data_scorer2.json`) and shows the Comparison summary statistics (agreement, Cohen's kappa, confusion matrix).
- Scene 12 demos every Jump button on the Navigation bar; it does not need a Comparison scoring. Hover vs click is decided at film time: a button that is disabled or has no target from the current Epoch is only hovered, with a caption explaining it would jump to one (displayed Epoch asserted unchanged); a button with a target is clicked and the Epoch asserted to move to it. No Epoch is cleared or staged by hand, so after GSSC "Next unscored" and "Next human-scored" are hover-only, while "Next stage transition", "Next event" and (with scene 11) "Next disagreement" are clicked. "Next uncertain" is always pressed, reported rather than asserted if GSSC produced no uncertain Epoch. Scene 12 can be left out of the registry without affecting 11 and 13.
- Scene 13 removes the Comparison scoring again (statistics action disabled).
- Scene 14 imports an Overlay signal through File > Import Overlay (EEGLAB) via a real, non-native file dialog filmed at the same temp folder — the cursor clicks `example_data_overlay.mat`, then Open; the Overlay signal is shown drawn over the Displayed signal on the current Epoch for a few seconds, then removed. No Epoch roaming.
- See the docstring of `make_video.py` for the scene contract and helpers.
