import os
from PySide6.QtWidgets import QFileDialog, QMessageBox

from .displayed_signal import settings_changed
from .load_wrapper import load_single
from .resample import resample_to_rate
from utilities.busy_indicator import run_busy
from utilities.overlay_state import drop_overlay_signal, set_checked_silently


_DATATYPE_FILTER = {
    "eeglab": "*.mat",
    "r09": "*.r09",
    "edf": "*.edf",
    "edfvolt": "*.edf",
}


def _in_primary_file_order(eeg_data_ovl, names_ovl, names_primary):
    """Overlay rows in the primary recording's file signal order, so that each
    channel's Signal_index points at the same signal in both. Raises ValueError if
    the overlay file does not hold the same signals."""
    if list(names_ovl) == list(names_primary):
        return eeg_data_ovl
    if sorted(names_ovl) != sorted(names_primary) or len(set(names_primary)) != len(names_primary):
        raise ValueError(
            "The signal names in the overlay file do not match the primary recording's signals."
        )
    return eeg_data_ovl[[list(names_ovl).index(name) for name in names_primary]]


def import_overlay_signal(ui, datatype):
    if getattr(ui, "eeg_data", None) is None:
        return

    filepath, _ = QFileDialog.getOpenFileName(
        None, "Open Overlay Signal File", ui.default_data_path, _DATATYPE_FILTER[datatype]
    )
    if not filepath:
        return
    ui.default_data_path = os.path.dirname(filepath)

    prefix, _ = os.path.splitext(filepath)

    def work():
        eeg_data_ovl, srate_ovl, channel_names_ovl, _ = load_single(prefix, datatype)
        # Bring the overlay to the primary recording's rate before validation
        eeg_data_ovl = resample_to_rate(eeg_data_ovl, srate_ovl, ui.config[0]["Sampling_rate_hz"])

        if eeg_data_ovl.shape[1] != ui.eeg_data.shape[1]:
            raise ValueError(
                f"Sample count mismatch: the primary recording has {ui.eeg_data.shape[1]} samples, "
                f"but '{os.path.basename(filepath)}' has {eeg_data_ovl.shape[1]} samples. Both "
                f"recordings must have the same number of samples to be overlaid."
            )
        return _in_primary_file_order(eeg_data_ovl, channel_names_ovl, ui.signal_names)

    def done(eeg_data_ovl):
        ui.eeg_data_ref = eeg_data_ovl
        ui.action_remove_overlay.setEnabled(True)
        ui.menu_analyze_source.setEnabled(True)
        ui.action_show_overlay.setEnabled(True)
        set_checked_silently(ui.action_show_overlay, True)
        ui.show_overlay = True
        settings_changed(ui)

    def failed(e):
        QMessageBox.critical(None, "Overlay loading error", str(e))

    run_busy(ui, "Importing overlay…", work, done, failed)


def remove_overlay_signal(ui):
    if getattr(ui, "eeg_data_ref", None) is None:
        return

    drop_overlay_signal(ui)
    settings_changed(ui)
