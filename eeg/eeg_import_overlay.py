import os
from PySide6.QtWidgets import QFileDialog, QMessageBox

from .load_wrapper import load_single
from .resample import resample_to_rate
from .align_channels import align_channels_to_config
from .rebuild_display import rebuild_eeg_data_display
from utilities.busy_indicator import run_busy


_DATATYPE_FILTER = {
    "eeglab": "*.mat",
    "r09": "*.r09",
    "edf": "*.edf",
    "edfvolt": "*.edf",
}


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

        non_derived_names = {ch["Channel_name"] for ch in ui.config[1] if not ch.get("derived", False)}
        if set(channel_names_ovl) != non_derived_names:
            raise ValueError(
                "The channel names in the overlay file do not match the primary recording's channels."
            )

        ui.eeg_data_ref = align_channels_to_config(eeg_data_ovl, channel_names_ovl, ui.config)
        rebuild_eeg_data_display(ui)

    def done(_):
        ui.action_remove_overlay.setEnabled(True)
        ui.menu_analyze_source.setEnabled(True)
        ui.action_show_overlay.setEnabled(True)
        ui.action_show_overlay.setChecked(True)  # triggers redraw with the overlay visible

    def failed(e):
        QMessageBox.critical(None, "Overlay loading error", str(e))

    run_busy(ui, "Importing overlay…", work, done, failed)


def remove_overlay_signal(ui):
    if getattr(ui, "eeg_data_ref", None) is None:
        return

    ui.eeg_data_ref = None
    ui.eeg_data_display_ref = None

    ui.action_remove_overlay.setEnabled(False)
    ui.menu_analyze_source.setEnabled(False)
    ui.action_show_overlay.setChecked(False)  # triggers redraw with the overlay hidden
    ui.action_show_overlay.setEnabled(False)
    ui.action_analyze_original.setChecked(True)  # triggers analysis panels back to the primary signal
