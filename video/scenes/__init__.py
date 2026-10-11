"""Scene registry: one line per scene, in film order. Each entry is the name of a module
in this folder exposing `run(ctx)` and `check(ctx)` (see video/make_video.py)."""

SCENES = [
    "s01_spectrogram_clicks",
    "s02_swa_slider",
    "s11_overlay_signal",
    "s12_configuration_tour",
]
