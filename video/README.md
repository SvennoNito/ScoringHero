# Walk-through video

Renders a silent, captioned 1920x1080, 30 fps walk-through of ScoringHero by driving the real main window with Qt input events (issue #55).

```
uv run --extra gssc python video/make_video.py            # -> video/scoringhero_walkthrough.mp4
uv run --extra gssc python video/make_video.py --smoke    # 640x360, 6 fps, state asserted after each scene
uv run --extra gssc python video/make_video.py --scenes s01 s02   # only these scenes
```

- `--extra gssc` is required: scene 4 runs the GSSC Autoscorer for real.
- Scenes run in film order (`video/scenes/__init__.py`); later scenes depend on earlier ones (scene 7 needs the spindles of scene 5, scene 10 derives its Comparison scoring from the Primary scoring after scene 8), so `--scenes` subsets only work for independent scenes.
- Runs on a temp copy of `example_data`; tracked files are never changed.
- The smoke run is manual (needs GSSC, takes a few minutes); it is not part of pytest or the commit hook.
- Generated files in `video/` (`.mp4`, `.json`, `.mat`, `.pdf`) are gitignored.
- Scene 6 seeds targets off camera so every Jump button has somewhere to go: a few unscored Epochs, a few human-scored Epochs, one uncertain Epoch and a temporary Comparison scoring that disagrees on a few Epochs. Everything is restored at the end of the scene, but the temporary Comparison scoring is visible in the Hypnogram while it runs.
- See the docstring of `make_video.py` for the scene contract and helpers.
