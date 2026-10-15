from PySide6.QtWidgets import QMessageBox

from .refresh_gui import refresh_gui


def clear_all_stages(ui):
    """Unscore every epoch of the primary scoring after confirmation. Events and the
    comparison scoring are untouched."""
    if getattr(ui, "eeg_data_display", None) is None:
        QMessageBox.warning(None, "No data loaded", "Please load EEG data first.")
        return

    n_scored = sum(stage is not None for stage in ui.scoring.stages())
    answer = QMessageBox.question(
        None,
        "Clear all stages",
        f"Clear all {n_scored} scored epochs?\n\nThis cannot be undone.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    if answer != QMessageBox.Yes:
        return

    ui.scoring.set(range(len(ui.scoring)), None)
    ui.HypnogramWidget.update_hypnogram(ui)
    ui.save_scoring()
    refresh_gui(ui)
