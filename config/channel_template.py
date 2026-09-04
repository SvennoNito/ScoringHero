"""Global channel-configuration template.

Channel-level settings (re-reference, filters, polarity flip, derived/re-referenced
channels added via the config window, display color/scale) are normally scoped to
one recording -- they live in `{filename}.config.json` next to the EEG file. That
means a freshly opened recording that has never been scored before always starts
from scratch, even if the user just spent time setting up the exact same montage
on a previous file.

This module persists the most recently saved `config[1]` (the per-channel list) as
a single global template, independent of any one recording, and applies it to new
recordings that don't have their own config.json yet. Matching is by channel name,
so it only takes effect where the new file's montage overlaps with the saved one.

Storage location mirrors `scoring/open_nidra_window.py`'s settings file: next to
the executable in a packaged build (ui.app_path is a temporary extraction dir
there), otherwise next to the source (ui.app_path), with the user's home directory
as a fallback for read-only install locations.
"""

import json
import os
import sys

_TEMPLATE_FILENAME = "channel_template.json"


def _is_frozen():
    return bool(
        getattr(sys, "frozen", False)
        or hasattr(sys, "_MEIPASS")
        or os.environ.get("NUITKA_ONEFILE_PARENT")
    )


def _template_paths(app_path):
    directories = []
    if _is_frozen():
        directories.append(os.path.dirname(os.path.abspath(sys.executable)))
    elif app_path:
        directories.append(app_path)
    directories.append(os.path.join(os.path.expanduser("~"), ".scoringhero"))

    return [os.path.join(directory, _TEMPLATE_FILENAME) for directory in directories]


def load_channel_template(app_path):
    """Return the saved per-channel settings list (config[1] shape), or [] if none."""
    for path in _template_paths(app_path):
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as handle:
                data = json.load(handle)
            if isinstance(data, list):
                return data
        except Exception:
            continue
    return []


def save_channel_template(app_path, config):
    """Persist config[1] as the default channel template for future recordings."""
    for path in _template_paths(app_path):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as handle:
                json.dump(config[1], handle, indent=2)
            return
        except Exception:
            continue


def apply_channel_template(configuration_settings, template, channel_names):
    """Overlay a saved global channel template onto freshly-built default settings.

    Non-derived channels whose name matches a saved entry inherit that entry's
    re-reference, filter, flip and display settings wholesale. Derived channels
    (re-referenced channels added via the config window, not present in the raw
    file) are recreated from the template whenever their source channel is among
    the (possibly just-overlaid) non-derived channels.
    """
    if not template:
        return configuration_settings

    by_name = {}
    for chan in template:
        by_name.setdefault(chan.get("Channel_name"), chan)

    updated_non_derived = []
    for chan in configuration_settings[1]:
        saved = by_name.get(chan["Channel_name"])
        if saved and not saved.get("derived", False):
            merged = dict(saved)
            merged["Channel_name"] = chan["Channel_name"]
            updated_non_derived.append(merged)
        else:
            updated_non_derived.append(chan)

    available_names = {chan["Channel_name"] for chan in updated_non_derived}
    derived = [
        dict(chan) for chan in template
        if chan.get("derived", False) and chan.get("source_channel") in available_names
    ]

    configuration_settings[1] = updated_non_derived + derived
    return configuration_settings
