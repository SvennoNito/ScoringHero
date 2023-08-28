from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QToolBar,
    QLabel,
    QSpinBox,
    QWidget,
    QPushButton,
    QSizePolicy,
)
from utilities import *


def setup_toolbar(ui, MainWindow):
    toolbar = QToolBar(MainWindow)
    toolbar.setObjectName("toolbar")
    MainWindow.addToolBar(Qt.TopToolBarArea, toolbar)

    # Jump to epoch spinbox
    toolbar.addWidget(QLabel("Jump to epoch:"))
    ui.toolbar_jump_to_epoch = QSpinBox()
    ui.toolbar_jump_to_epoch.setMinimum(1)
    ui.toolbar_jump_to_epoch.valueChanged.connect(lambda value, ui=ui: jump_to_epoch(value, ui))
    ui.toolbar_jump_to_epoch.editingFinished.connect(ui.toolbar_jump_to_epoch.clearFocus)
    toolbar.addWidget(ui.toolbar_jump_to_epoch)

    # Space
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    spacer.setFixedWidth(10)
    toolbar.addWidget(spacer)

    # Next unscored epoch button
    ui.tool_nextunscored = QPushButton("Next unscored epoch")
    ui.tool_nextunscored.clicked.connect(lambda: first_unscored_epoch(ui))
    toolbar.addWidget(ui.tool_nextunscored)
    toolbar.addWidget(spacer)

    # Next uncertain epoch button
    ui.tool_nextuncertain = QPushButton("Next uncertain epoch")
    ui.tool_nextuncertain.clicked.connect(lambda: first_uncertain_stage(ui))
    toolbar.addWidget(ui.tool_nextuncertain)
    toolbar.addWidget(spacer)

    # Next transition button
    ui.tool_nexttransition = QPushButton("Next transition")
    ui.tool_nexttransition.clicked.connect(lambda: next_stage_transition(ui))
    toolbar.addWidget(ui.tool_nexttransition)
    # toolbar.addWidget(spacer)
