import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QSizePolicy, QSpinBox, QStackedWidget

from style.roles import set_role
from utilities.epoch_status import epoch_status
from widgets.stageBadge import StageBadge, stage_text_color, stage_tint


class _ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled():
            self.clicked.emit()


class _EpochSpinBox(QSpinBox):
    cancelled = Signal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancelled.emit()
        else:
            super().keyPressEvent(event)


class EpochReadout(QStackedWidget):
    """'Epoch 12 / 767'; a click turns it into a spin box to type an epoch number into.
    Enter (or leaving the box) jumps; the numbers are 1-based like the display."""

    epochChosen = Signal(int)
    editingDone = Signal()

    def __init__(self):
        super().__init__()
        self._epoch_number = 1
        self.label = _ClickableLabel("Epoch")
        self.label.setCursor(Qt.PointingHandCursor)
        self.label.setToolTip("Click to jump to an epoch")
        set_role(self.label, "epoch-readout")

        self.spin = _EpochSpinBox()
        self.spin.setMinimum(1)
        self.spin.setPrefix("Epoch ")
        self.spin.setKeyboardTracking(False)  # jump on Enter, not on every digit

        self.addWidget(self.label)
        self.addWidget(self.spin)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.setEnabled(False)

        self.label.clicked.connect(self._start_editing)
        self.spin.valueChanged.connect(self.epochChosen)
        self.spin.editingFinished.connect(self._stop_editing)
        self.spin.cancelled.connect(self._cancel_editing)

    def set_total(self, total):
        self.spin.setMaximum(total)
        self.spin.setSuffix(f" / {total}")

    def show_epoch(self, epoch):
        """Show the 0-based `epoch`."""
        self._epoch_number = epoch + 1
        self.label.setText(f"Epoch {epoch + 1} / {self.spin.maximum()}")

    def _start_editing(self):
        self.spin.blockSignals(True)
        self.spin.setValue(self._epoch_number)
        self.spin.blockSignals(False)
        self.setCurrentWidget(self.spin)
        self.spin.setFocus()
        self.spin.selectAll()

    def _stop_editing(self):
        self.setCurrentWidget(self.label)
        self.editingDone.emit()

    def _cancel_editing(self):
        self.spin.blockSignals(True)
        self.spin.setValue(self._epoch_number)
        self.spin.blockSignals(False)
        self._stop_editing()


class StatusReadout:
    """Fills the status bar: epoch, stage, comparison stage, confidence and clock time on
    the left; recording name and scoring state on the right. The stage is also shown by a
    StageBadge over the signal panel (optional, movable)."""

    def __init__(self, statusbar, signal_panel):
        self.epoch = EpochReadout()
        self.stage_badge = StageBadge(signal_panel)
        self.stage = QLabel()
        self.comparison = QLabel()
        self.confidence = QLabel()
        self.clock = QLabel()
        self.state = QLabel()
        self.file = QLabel()
        for widget in (self.epoch, self.stage, self.comparison, self.confidence, self.clock):
            statusbar.addWidget(widget)
        statusbar.addPermanentWidget(self.state)
        statusbar.addPermanentWidget(self.file)

    def update(self, ui):
        status = epoch_status(ui)
        self.epoch.show_epoch(ui.this_epoch)
        self.stage.setText(status.stage)
        self.stage.setStyleSheet(
            f"background: {stage_tint(status.stage)}; color: {stage_text_color(status.stage)};"
            "border-radius: 4px; padding: 0 8px; font-weight: 700;"
        )
        badge = self.stage_badge
        badge.setVisible(ui.config[0].get("Show_stage_badge", True))
        badge.show_stage(
            status.stage, status.comparison_stage, status.disagrees,
            ui.config[0].get("Stage_badge_position", [0.5, 0.5]), ui.config[0].get("Stage_badge_size", 24),
        )
        self.comparison.setText(status.comparison or "")
        self.comparison.setVisible(status.comparison is not None)
        set_role(self.comparison, "error" if status.disagrees else None)
        self.confidence.setText(status.confidence)
        self.clock.setText(status.clock)

        state = []
        if ui.scoring_save_failed:
            state.append("Unsaved changes")
        if ui.scoring_comparison is not None:
            state.append(f"Comparison: {ui.comparison_name}")
        self.state.setText(" · ".join(state))
        self.state.setVisible(bool(state))
        set_role(self.state, "error" if ui.scoring_save_failed else None)
        eeg = getattr(ui, "eeg_file_name", "")
        extra = getattr(ui, "eeg_extra_files", 0)
        eeg_text = f"{eeg} (+{extra})" if extra else eeg
        self.file.setText(f"EEG: {eeg_text}  ·  Scoring: {os.path.basename(ui.filename)}.json")
