"""Scene registry: one line per scene, in film order. Each entry is the name of a module
in this folder exposing `run(ctx)` and `check(ctx)` (see video/make_video.py)."""

SCENES = [
    "s01_load_recording",
    "s02_manual_stages",
    "s04_swa_slider",
    "s05_highpass_filter",
    "s06_gssc",
    "s07_spindle_detection",
    "s08_events_tab_rename",
    "s09_arousal_event",
    "s10_periodogram",
    "s11_sleep_report",
    "s12_comparison_scoring",
    "s13_overlay_signal",
    "s14_configuration_tour",
]
