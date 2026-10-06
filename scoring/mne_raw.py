"""Build an mne RawArray that survives Nuitka compilation."""


def raw_array(data, info):
    """Return `mne.io.RawArray(data, info)`.

    Nuitka-compiled frames omit 'self' from f_locals, which crashes MNE's
    `_get_argvalues` (frame introspection, KeyError: 'self'). Patch it to
    return None while constructing — `_init_kwargs` is only used for repr.
    `mne.io.base` imports the function by name, so patch that binding.
    """
    import mne.io.base as mne_base
    from mne.io import RawArray

    original = mne_base._get_argvalues
    mne_base._get_argvalues = lambda: None
    try:
        return RawArray(data, info, verbose=False)
    finally:
        mne_base._get_argvalues = original
