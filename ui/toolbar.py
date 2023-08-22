from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolBar, QLabel, QSpinBox, QWidget, QPushButton, QSizePolicy

def setup_toolbar(ui, MainWindow):
    toolbar = QToolBar(MainWindow)
    toolbar.setObjectName("toolbar")
    MainWindow.addToolBar(Qt.TopToolBarArea, toolbar)

    # Jump to epoch spinbox
    toolbar.addWidget(QLabel("Jump to epoch:")) 
    ui.tool_epochjump = QSpinBox() 
    #ui.tool_epochjump.valueChanged.connect(ui.jump_to_epoch)
    toolbar.addWidget(ui.tool_epochjump)

    # Space
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    spacer.setFixedWidth(10)        
    toolbar.addWidget(spacer)    

    # Next unscored epoch button     
    ui.tool_nextunscored = QPushButton("Next unscored epoch")
    #ui.tool_nextunscored.clicked.connect(ui.jump_to_unscored_epoch)
    toolbar.addWidget(ui.tool_nextunscored)
    toolbar.addWidget(spacer) 

    # Next uncertain epoch button     
    ui.tool_nextuncertain = QPushButton("Next uncertain epoch")
    #ui.tool_nextuncertain.clicked.connect(ui.jump_to_uncertain_epoch)
    toolbar.addWidget(ui.tool_nextuncertain)
    toolbar.addWidget(spacer)         

    # Next transition button
    ui.tool_nexttransition    = QPushButton("Next transition")
    #ui.tool_nexttransition.clicked.connect(ui.jump_to_transition)
    toolbar.addWidget(ui.tool_nexttransition)
    #toolbar.addWidget(spacer)     