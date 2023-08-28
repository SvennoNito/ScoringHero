from PySide6.QtGui import QAction, QColor
from PySide6.QtCore import QRect, QMetaObject
from PySide6.QtWidgets import QWidget, QGridLayout, QMenuBar, QMenu, QStatusBar, QVBoxLayout

from .toolbar import setup_toolbar
from .menu import setup_menu
from widgets import *
from utilities import *
from data_handling import *
from mouse_click import *
from paint_event import *

@timing_decorator
def setup_ui(ui, MainWindow):
    MainWindow.setObjectName("MainWindow")
    MainWindow.resize(800, 600)
    ui.centralwidget = QWidget(MainWindow)
    ui.centralwidget.setObjectName("centralwidget")
    # MainWindow.showMaximized()

    # set the grid layout
    layout          = QGridLayout()
    ui.centralwidget.setLayout(layout) 

    # Build widgets
    ui.BackgroundWidget = BackgroundWidget(ui.centralwidget)
    ui.SignalWidget     = SignalWidget(ui.centralwidget)
    ui.DisplayedEpochWidget = DisplayedEpochWidget(ui.SignalWidget.axes)
    ui.SpectogramWidget = SpectogramWidget(ui.centralwidget)
    ui.HypnogramWidget = HypnogramWidget(ui.centralwidget)
    ui.SpectogramSlider = SpectogramSlider(ui.centralwidget)
    ui.HypnogramSlider = HypnogramSlider(ui.centralwidget)
    ui.RectanglePower = RectanglePower(ui.centralwidget)
    ui.PaintEventWidget = PaintEventWidget()

    # Make widgets react to mouse click
    ui.SpectogramWidget.graphics.scene().sigMouseClicked.connect(lambda event, ui=ui: click_on_spectogram(event, ui))
    ui.HypnogramWidget.axes.scene().sigMouseClicked.connect(lambda event, ui=ui: click_on_hypnogram(event, ui))
    ui.SpectogramSlider.slider.valueChanged.connect(lambda value, ui=ui: move_spectogram_slider(value, ui))
    ui.HypnogramSlider.slider.valueChanged.connect(lambda value, ui=ui: move_swa_slider(value, ui))
    ui.PaintEventWidget.changesMade.connect(lambda ui=ui: paint_event_wrapper(ui))


    # Layout
    layout.addWidget(ui.BackgroundWidget.axes,             10,  0,  85,  100)
    layout.addWidget(ui.SignalWidget.axes,                 10,  0,  85,  101)
    layout.addWidget(ui.PaintEventWidget,                  10,  0,  85,  101)
    layout.addWidget(ui.SpectogramWidget.graphics,          0,  0,  10,   55)
    layout.addWidget(ui.SpectogramSlider.slider,            1, 55,   8,    1)
    layout.addWidget(ui.HypnogramWidget.axes,               0, 56,  10,   30)
    layout.addWidget(ui.HypnogramSlider.slider,             1, 86,   8,    1)
    layout.addWidget(ui.RectanglePower.axes,                0, 87,  10,   13)

    # menu
    MainWindow.setCentralWidget(ui.centralwidget)
    ui.menu = QMenuBar(MainWindow)
    ui.menu.setGeometry(QRect(0, 0, 800, 22))
    ui.menu.setObjectName("menu")

    # File menu
    ui.menu_file = QMenu(ui.menu)
    ui.menu_file.setObjectName("menu_file")    
    ui.menu.addAction(ui.menu_file.menuAction())  

    # Load EEG submenu
    ui.submenu_load_eeg = QMenu("Load EEG", ui.menu_file)
    ui.submenu_load_eeg.setObjectName("submenu_load_eeg")
    ui.menu_file.addMenu(ui.submenu_load_eeg)    
    ui.action_load_eeglab = QAction("", ui)
    ui.action_load_eeglab.setObjectName("action_load_eeglab")
    ui.action_load_eeglab.triggered.connect(lambda: ui.load_eeg(datatype = 'eeglab'))
    ui.submenu_load_eeg.addAction(ui.action_load_eeglab)      
 
    ui.action_load_scoring = QAction(MainWindow)
    ui.action_load_scoring.setObjectName("action_load_scoring")
    #ui.action_load_scoring.triggered.connect(lambda: ui.load_scorin_file_from_menu())
    ui.menu_file.addAction(ui.action_load_scoring)
    ui.action_save_scoring = QAction(MainWindow)
    ui.action_save_scoring.setObjectName("action_save_scoring")
    ui.action_save_scoring.triggered.connect(lambda: write_scoring_popup(ui))
    ui.menu_file.addAction(ui.action_save_scoring)  

    # Edits menu
    ui.menu_edit           = QMenu(ui.menu)
    ui.menu_edit.setObjectName("menu_edit")
    ui.menu.addAction(ui.menu_edit.menuAction())

    ui.action_edit_channels     = QAction(MainWindow)
    ui.action_edit_channels.setObjectName("action_edit_channels")
    #ui.action_edit_channels.triggered.connect(lambda: ui.scaleChannels())
    ui.menu_edit.addAction(ui.action_edit_channels)
    ui.action_edit_annotations  = QAction(MainWindow)
    ui.action_edit_annotations.setObjectName("action_edit_annotations")
    #ui.action_edit_annotations.triggered.connect(lambda: ui.edit_annotations())
    ui.menu_edit.addAction(ui.action_edit_annotations)
    ui.action_edit_config          = QAction(MainWindow)
    ui.action_edit_config.setObjectName("action_edit_config")     
    #ui.action_edit_config.triggered.connect(lambda: ui.configuration_pop_up())      
    ui.menu_edit.addAction(ui.action_edit_config)

    # Sleep stages menu
    ui.menu_stages         = QMenu(ui.menu)
    ui.menu_stages.setObjectName("menu_stages")
    ui.menu.addAction(ui.menu_stages.menuAction())

    ui.action_N1           = QAction(MainWindow)
    ui.action_N1.setObjectName("action_N1")
    ui.action_N1.triggered.connect(lambda stage="N1", ui=ui: score_stage(stage, ui))
    ui.menu_stages.addAction(ui.action_N1)
    ui.action_N2           = QAction(MainWindow)
    ui.action_N2.setObjectName("action_N2")
    ui.action_N2.triggered.connect(lambda stage="N2", ui=ui: score_stage(stage, ui))
    ui.menu_stages.addAction(ui.action_N2)
    ui.action_N3           = QAction(MainWindow)
    ui.action_N3.setObjectName("action_N3")
    ui.action_N3.triggered.connect(lambda stage="N3", ui=ui: score_stage(stage, ui))
    ui.menu_stages.addAction(ui.action_N3)
    ui.action_wake         = QAction(MainWindow)
    ui.action_wake.setObjectName("action_wake")
    ui.action_wake.triggered.connect(lambda stage="Wake", ui=ui: score_stage(stage, ui))
    ui.menu_stages.addAction(ui.action_wake)
    ui.action_REM          = QAction(MainWindow)
    ui.action_REM.setObjectName("action_REM")
    ui.action_REM.triggered.connect(lambda stage="REM", ui=ui: score_stage(stage, ui))
    ui.menu_stages.addAction(ui.action_REM)        
    ui.action_express_uncertainty  = QAction(MainWindow)
    ui.action_express_uncertainty.setObjectName("action_express_uncertainty")  
    #ui.action_express_uncertainty.triggered.connect(lambda: ui.scoring_uncertainty())      
    ui.menu_stages.addAction(ui.action_express_uncertainty)
    ui.menu_stages.addSeparator()
    ui.action_label_artefact    = QAction(MainWindow)
    ui.action_label_artefact.setObjectName("action_label_artefact")   
    #ui.action_label_artefact.triggered.connect(lambda: ui.label_artefacts())   
    ui.menu_stages.addAction(ui.action_label_artefact)
    ui.action_zoon_on_EEG    = QAction(MainWindow)
    ui.action_zoon_on_EEG.setObjectName("action_zoon_on_EEG")   
    #ui.action_zoon_on_EEG.triggered.connect(lambda: ui.zoom_on_selected_eeg())   
    ui.menu_stages.addAction(ui.action_zoon_on_EEG)

    # Bring together
    MainWindow.setMenuBar(ui.menu)
    ui.statusbar = QStatusBar(MainWindow)
    ui.statusbar.setObjectName("statusbar")
    MainWindow.setStatusBar(ui.statusbar)
    setup_menu(ui, MainWindow)
    QMetaObject.connectSlotsByName(MainWindow)

    # *** Setup toolbar ***
    setup_toolbar(ui, MainWindow)
    
    # Makes GUI listen to key strokes
    MainWindow.keyPressEvent = ui.keyPressEvent     