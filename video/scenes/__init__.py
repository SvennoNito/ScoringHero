"""Scene registry: one line per scene, in film order. Each entry is the name of a module
in this folder exposing `run(ctx)` and `check(ctx)` (see video/make_video.py)."""

SCENES = [
    "s01_load_recording",
    "s02_manual_stages",
    "s03_swa_slider",
    "s04_highpass_filter",
    "s05_gssc",
    "s06_spindle_detection",
    "s07_events_tab_rename",
    "s08_arousal_event",
    "s09_periodogram",
    "s10_sleep_report",
    "s11_comparison_scoring",
    "s14_overlay_signal",
    "s15_configuration_tour",
]
