"""Build an mne RawArray that survives Nuitka compilation."""


def raw_array(data, info):
    """Return `mne.io.RawArray(data, info)`.

    Nuitka-compiled frames omit 'self' from f_locals, which crashes MNE's
    `_get_argvalues` (frame introspection, KeyError: 'self'). Stub it out
    while constructing — `_init_kwargs` is only used for repr. Patch both
    bindings: CPython calls the name `mne.io.base` imported, the Nuitka build
    resolves it through `mne.utils.misc`.
    """
    import mne.io.base as mne_base
    import mne.utils.misc as mne_misc
    from mne.io import RawArray

    modules = (mne_base, mne_misc)
    originals = [module._get_argvalues for module in modules]
    for module in modules:
        module._get_argvalues = lambda: None
    try:
        return RawArray(data, info, verbose=False)
    finally:
        for module, original in zip(modules, originals):
            module._get_argvalues = original
