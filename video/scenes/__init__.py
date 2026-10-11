"""Scene registry: one line per scene, in film order. Each entry is the name of a module
in this folder exposing `run(ctx)` and `check(ctx)` (see video/make_video.py)."""

SCENES = [
    "s00_load_recording",
    "s00b_manual_stages",
    "s01_spectrogram_clicks",
    "s02_swa_slider",
    "s03_highpass_filter",
    "s04_gssc",
    "s05_spindle_detection",
    "s05b_events_tab_rename",
    "s07_manual_spindles",
    "s09_sleep_report",
    "s10_comparison_scoring",
    "s11_overlay_signal",
    "s12_configuration_tour",
]
