import copy
import os
import pickle

from config.channel_settings import rebuild_fingerprint, rename_channel
from .write_cache import write_cache


def rename_in_cache(ui, old_name, new_name):
    """Follow a channel rename (already applied to ui.config) in the on-disk cache, so
    the cached analysis data still matches on reopening. A rename changes no sample:
    only the channel names the cache was validated with are re-pointed."""
    filename = f"{ui.filename}.cache.pkl"
    if not os.path.exists(filename):
        return
    with open(filename, "rb") as file:
        cache = pickle.load(file)

    channels_before = copy.deepcopy(ui.config[1])
    rename_channel(channels_before, {}, new_name, old_name)
    if cache.get("manipulation_fingerprint") == rebuild_fingerprint(channels_before):
        cache["manipulation_fingerprint"] = rebuild_fingerprint(ui.config[1])
    if cache.get("Channel_for_spectogram") == old_name:
        cache["Channel_for_spectogram"] = new_name
    if cache.get("epoch_periodogram", {}).get("channel") == old_name:
        cache["epoch_periodogram"]["channel"] = new_name
    write_cache(ui, cache)
