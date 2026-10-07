from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QLabel

MARGIN = 10

# (background, text) per stage; same palette as the sleep report
STAGE_COLORS = {
    "Wake": ("#8bbf56", "#10200a"),
    "N1": ("#aabcce", "#10202e"),
    "N2": ("#405c79", "#ffffff"),
    "N3": ("#0b1c2c", "#ffffff"),
    "REM": ("#dc5050", "#ffffff"),
}
UNSCORED_COLORS = ("rgba(120, 128, 140, 170)", "#ffffff")
DISAGREE_BORDER = "#c0392b"


class StageBadge(QLabel):
    """Large stage chip floating at the top centre of `panel` (the signal panel).
    Shows the stage of the displayed epoch; 'N2 vs N3' with a red border when the
    comparison scoring disagrees."""

    def __init__(self, panel):
        super().__init__(panel)
        self.setAlignment(Qt.AlignCenter)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        panel.installEventFilter(self)

    def show_stage(self, stage, comparison_stage=None, disagrees=False):
        text = f"{stage} vs {comparison_stage}" if disagrees else stage
        background, color = STAGE_COLORS.get(stage, UNSCORED_COLORS)
        border = DISAGREE_BORDER if disagrees else "transparent"
        self.setStyleSheet(
            f"background: {background}; color: {color}; border: 3px solid {border};"
            "border-radius: 10px; padding: 4px 18px; font-size: 28px; font-weight: 700;"
        )
        self.setText(text)
        self.adjustSize()
        self._place()

    def _place(self):
        self.move((self.parentWidget().width() - self.width()) // 2, MARGIN)
        self.raise_()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self._place()
        return False
