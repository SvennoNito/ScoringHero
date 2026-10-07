from functools import partial

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar

from scoring_model.scoring import UNCERTAIN_BELOW
from style.icons import icon
from utilities.epoch_disagreement import next_disagreement_epoch
from utilities.epoch_human import next_human_epoch
from utilities.epoch_transition import stage_transition
from utilities.epoch_uncertain import next_uncertain_stage
from utilities.epoch_unscored import next_unscored_epoch
from utilities.jump_to_event import jump_to_event

NEEDS_RECORDING = "open a recording first"
NEEDS_COMPARISON = "load a comparison scoring first"

# ui attribute, button name, tooltip headline (rich text), tooltip explanation, icon, jump,
# why it can be disabled
JUMP_BUTTONS = [
    ("tool_nextunscored", "Next unscored", "Jump to next <b>unscored</b> epoch",
     "Epoch without a stage",
     "circle-dashed", next_unscored_epoch, NEEDS_RECORDING),
    ("tool_nextuncertain", "Next uncertain", "Jump to next <b>uncertain</b> epoch",
     f"Epoch whose confidence is below {UNCERTAIN_BELOW}",
     "circle-question-mark", next_uncertain_stage, NEEDS_RECORDING),
    ("tool_nexttransition", "Next stage transition", "Jump to next <b>stage transition</b>",
     "Epoch whose stage differs from the current one (unscored counts as a stage)",
     "arrow-left-right", stage_transition, NEEDS_RECORDING),
    ("tool_nextevent", "Next event", "Jump to next epoch with an <b>event</b>",
     "Epoch that contains an event",
     "flag", jump_to_event, NEEDS_RECORDING),
    ("tool_nexthuman", "Next human-scored", "Jump to next <b>human-scored</b> epoch",
     "Epoch whose stage you set yourself",
     "user", next_human_epoch, NEEDS_RECORDING),
    ("tool_nextdisagreement", "Next disagreement", "Jump to next <b>disagreement</b> epoch",
     "Epoch whose stage differs from the comparison scoring",
     "git-compare-arrows", next_disagreement_epoch, NEEDS_COMPARISON),
]


def _show_tooltip(action, headline, explanation, reason):
    tip = f"{headline}<br><i>{explanation}</i>"
    if not action.isEnabled():
        tip += f"<br>Unavailable: {reason}"
    if action.toolTip() != tip:
        action.setToolTip(tip)


def setup_navigation_bar(ui, MainWindow):
    """Vertical, icon-only bar on the left of the main window with one jump button per
    kind of epoch. Each button is a QAction stored on `ui` (disabled until it applies)."""
    bar = QToolBar("Navigation", MainWindow)
    bar.setObjectName("navigation_bar")
    bar.setOrientation(Qt.Vertical)
    bar.setMovable(False)
    bar.setFloatable(False)
    bar.setToolButtonStyle(Qt.ToolButtonIconOnly)
    bar.setIconSize(QSize(16, 16))
    MainWindow.addToolBar(Qt.LeftToolBarArea, bar)
    ui.navigation_bar = bar

    for attribute, name, headline, explanation, icon_name, jump, reason in JUMP_BUTTONS:
        action = QAction(icon(icon_name), name, bar)
        action.setEnabled(False)
        action.triggered.connect(lambda checked=False, jump=jump: jump(ui))
        action.changed.connect(partial(_show_tooltip, action, headline, explanation, reason))
        _show_tooltip(action, headline, explanation, reason)
        bar.addAction(action)
        # Reachable with Tab, but a click leaves focus on the plot so arrow keys keep working
        bar.widgetForAction(action).setFocusPolicy(Qt.TabFocus)
        setattr(ui, attribute, action)
