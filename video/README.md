# Walk-through video

Renders a silent, captioned 1920x1080, 30 fps walk-through of ScoringHero by driving the real main window with Qt input events (issue #55).

```
uv run --extra gssc python video/make_video.py            # -> video/scoringhero_walkthrough.mp4
uv run --extra gssc python video/make_video.py --smoke    # 640x360, 6 fps, state asserted after each scene
uv run --extra gssc python video/make_video.py --scenes s01 s02   # only these scenes
```

- `--extra gssc` is required: scene 6 runs the GSSC Autoscorer for real.
- Scenes run in film order (`video/scenes/__init__.py`); the film opens on the empty window and scene 1 loads the example recording through File > Load EEG with the cursor on the menus, via a real, non-native file dialog filmed at a temp folder named "... ScoringHero example" — the cursor clicks `example_data.mat`, then Open. Later scenes depend on earlier ones (scene 9 needs the spindles of scene 7, scene 12 derives its Comparison scoring from the Primary scoring after scene 10), so `--scenes` subsets only work for independent scenes.
- Runs on a temp copy of `example_data`; tracked files are never changed.
- The smoke run is manual (needs GSSC, takes a few minutes); it is not part of pytest or the commit hook.
- Generated files in `video/` (`.mp4`, `.json`, `.mat`, `.pdf`) are gitignored.
- Scene 12 imports a Comparison scoring through a real, filmed file dialog (`example_data_scorer2.json`), shows the Comparison summary statistics, then demos every Jump button. No Epoch is cleared or staged by hand: after GSSC every Epoch already has a Stage, so "Next unscored" and "Next human-scored" have no real target and are only hovered, with a caption explaining why. "Next stage transition", "Next event" and "Next disagreement" already have real targets (the GSSC-staged night, the spindle Events, and the Comparison scoring just imported) and are clicked for real. "Next uncertain" is reported rather than asserted if GSSC produced no uncertain Epoch.
- See the docstring of `make_video.py` for the scene contract and helpers.
