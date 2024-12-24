from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QToolBar,
    QLabel,
    QSpinBox,
    QWidget,
    QPushButton,
    QSizePolicy,
)
from utilities.jump_to_epoch import jump_to_epoch
from utilities.epoch_unscored import first_unscored_epoch
from utilities.epoch_uncertain import next_uncertain_stage
from utilities.epoch_transition import stage_transition
from utilities.jump_to_event import jump_to_event


def setup_toolbar(ui, MainWindow):
    toolbar = QToolBar(MainWindow)
    toolbar.setObjectName("toolbar")
    MainWindow.addToolBar(Qt.TopToolBarArea, toolbar)
    MainWindow.toolbar = toolbar

    # Jump to epoch spinbox
    toolbar.addWidget(QLabel("Jump to epoch:"))

    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    spacer.setFixedWidth(2)
    toolbar.addWidget(spacer)

    ui.toolbar_jump_to_epoch = QSpinBox()
    ui.toolbar_jump_to_epoch.setMinimum(1)
    ui.toolbar_jump_to_epoch.valueChanged.connect(lambda value, ui=ui: jump_to_epoch(value, ui))
    ui.toolbar_jump_to_epoch.editingFinished.connect(ui.toolbar_jump_to_epoch.clearFocus)
    ui.toolbar_jump_to_epoch.setEnabled(False)
    toolbar.addWidget(ui.toolbar_jump_to_epoch)

    # Space
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    spacer.setFixedWidth(20)
    toolbar.addWidget(spacer)

    # Next unscored epoch button
    toolbar.addWidget(QLabel(""))

    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    spacer.setFixedWidth(2)
    toolbar.addWidget(spacer)

    ui.tool_nextunscored = QPushButton("unscored")
    ui.tool_nextunscored.clicked.connect(lambda: [first_unscored_epoch(ui), ui.tool_nextunscored.clearFocus()])
    ui.tool_nextunscored.setEnabled(False) 
    toolbar.addWidget(ui.tool_nextunscored)

    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    spacer.setFixedWidth(2)
    toolbar.addWidget(spacer)

    # Next uncertain epoch button
    ui.tool_nextuncertain = QPushButton("uncertain")
    ui.tool_nextuncertain.clicked.connect(lambda: [next_uncertain_stage(ui), ui.tool_nextuncertain.clearFocus()])
    ui.tool_nextuncertain.setEnabled(False)
    toolbar.addWidget(ui.tool_nextuncertain)

    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    spacer.setFixedWidth(2)
    toolbar.addWidget(spacer)

    # Next transition button
    ui.tool_nexttransition = QPushButton("transition")
    ui.tool_nexttransition.clicked.connect(lambda: [stage_transition(ui), ui.tool_nexttransition.clearFocus()])
    ui.tool_nexttransition.setEnabled(False)
    toolbar.addWidget(ui.tool_nexttransition)

    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    spacer.setFixedWidth(2)
    toolbar.addWidget(spacer)

    # Next event button
    ui.tool_nextevent = QPushButton("event")
    ui.tool_nextevent.clicked.connect(lambda: [jump_to_event(ui), ui.tool_nextevent.clearFocus()])
    ui.tool_nextevent.setEnabled(False)
    toolbar.addWidget(ui.tool_nextevent)  