from PySide6.QtGui import QAction, QColor
from PySide6.QtCore import QRect, QMetaObject
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QMenuBar,
    QMenu,
    QStatusBar,
    QVBoxLayout,
)

from .toolbar import setup_toolbar
from .menu import setup_menu
from widgets import *
from utilities.timing_decorator import timing_decorator
from utilities.score_stage import score_stage 
from data_handling.write_scoring import write_scoring_popup
from mouse_click import *
from paint_event import *
from paint_event.zoom_on_selected_eeg import zoom_on_selected_eeg
from annotations.draw_box import draw_box
from utilities.scoring_uncertainty import scoring_uncertainty
from config.open_config_window import open_config_window
from data_handling.load_scoring import load_scoring_qdialog

@timing_decorator
def setup_ui(ui, MainWindow):
    ui.centralwidget = QWidget(MainWindow)
    ui.centralwidget.setObjectName("centralwidget")
    # MainWindow.showMaximized()

    # set the grid layout
    layout = QGridLayout()
    ui.centralwidget.setLayout(layout)

    # Build widgets
    ui.SignalWidget = SignalWidget(ui.centralwidget)
    ui.DisplayedEpochWidget = DisplayedEpochWidget(ui.SignalWidget.axes)
    ui.SpectogramWidget = SpectogramWidget(ui.centralwidget)
    ui.HypnogramWidget = HypnogramWidget(ui.centralwidget)
    ui.SpectogramSlider = SpectogramSlider(ui.centralwidget)
    ui.HypnogramSlider = HypnogramSlider(ui.centralwidget)
    ui.RectanglePower = RectanglePower(ui.centralwidget)
    ui.PaintEventWidget = PaintEventWidget()
    ui.AnnotationContainer = [AnnotationContainer(colorindex=counter, label=f'F{counter}') for counter in range(10)]


    # Make widgets react to mouse click
    ui.SpectogramWidget.graphics.scene().sigMouseClicked.connect(
        lambda event, ui=ui: click_on_spectogram(event, ui)
    )
    ui.HypnogramWidget.axes.scene().sigMouseClicked.connect(
        lambda event, ui=ui: click_on_hypnogram(event, ui)
    )
    ui.SpectogramSlider.slider.valueChanged.connect(
        lambda value, ui=ui: move_spectogram_slider(value, ui)
    )
    ui.HypnogramSlider.slider.valueChanged.connect(
        lambda value, ui=ui: move_swa_slider(value, ui)
    )
    ui.PaintEventWidget.changesMade.connect(lambda ui=ui: paint_event_wrapper(ui))

    # Layout
    layout.addWidget(ui.SignalWidget.axes, 10, 0, 85, 101)
    layout.addWidget(ui.PaintEventWidget, 10, 0, 85, 101)
    layout.addWidget(ui.SpectogramWidget.graphics, 0, 0, 10, 55)
    layout.addWidget(ui.SpectogramSlider.slider, 1, 55, 8, 1)
    layout.addWidget(ui.HypnogramWidget.axes, 0, 56, 10, 30)
    layout.addWidget(ui.HypnogramSlider.slider, 1, 86, 8, 1)
    layout.addWidget(ui.RectanglePower.axes, 0, 87, 10, 13)
   
    # menu
    MainWindow.setCentralWidget(ui.centralwidget)
    ui.menu = QMenuBar(MainWindow)
    ui.menu.setGeometry(QRect(0, 0, 800, 22))
    ui.menu.setObjectName("menu")
    ui.menu.setStyleSheet("QMenu::item:selected { color: gray; }")

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
    ui.action_load_eeglab.triggered.connect(lambda: ui.load_eeg(datatype="eeglab"))
    ui.submenu_load_eeg.addAction(ui.action_load_eeglab)

    ui.action_load_scoring = QAction(MainWindow)
    ui.action_load_scoring.setObjectName("action_load_scoring")
    ui.action_load_scoring.triggered.connect(lambda: load_scoring_qdialog(ui))
    ui.menu_file.addAction(ui.action_load_scoring)
    ui.action_save_scoring = QAction(MainWindow)
    ui.action_save_scoring.setObjectName("action_save_scoring")
    ui.action_save_scoring.triggered.connect(lambda: write_scoring_popup(ui))
    ui.menu_file.addAction(ui.action_save_scoring) 

    # Sleep stages menu
    ui.menu_stages = QMenu(ui.menu)
    ui.menu_stages.setObjectName("menu_stages")
    ui.menu.addAction(ui.menu_stages.menuAction())

    ui.action_N1 = QAction(MainWindow)
    ui.action_N1.setObjectName("action_N1")
    ui.action_N1.triggered.connect(lambda stage="N1", ui=ui: score_stage(stage, ui))
    ui.menu_stages.addAction(ui.action_N1)
    ui.action_N2 = QAction(MainWindow)
    ui.action_N2.setObjectName("action_N2")
    ui.action_N2.triggered.connect(lambda stage="N2", ui=ui: score_stage(stage, ui))
    ui.menu_stages.addAction(ui.action_N2)
    ui.action_N3 = QAction(MainWindow)
    ui.action_N3.setObjectName("action_N3")
    ui.action_N3.triggered.connect(lambda stage="N3", ui=ui: score_stage(stage, ui))
    ui.menu_stages.addAction(ui.action_N3)
    ui.action_wake = QAction(MainWindow)
    ui.action_wake.setObjectName("action_wake")
    ui.action_wake.triggered.connect(lambda stage="Wake", ui=ui: score_stage(stage, ui))
    ui.menu_stages.addAction(ui.action_wake)
    ui.action_REM = QAction(MainWindow)
    ui.action_REM.setObjectName("action_REM")
    ui.action_REM.triggered.connect(lambda stage="REM", ui=ui: score_stage(stage, ui))
    ui.menu_stages.addAction(ui.action_REM)
    ui.menu_stages.addSeparator()
    ui.action_express_uncertainty = QAction(MainWindow)
    ui.action_express_uncertainty.setObjectName("action_express_uncertainty")
    ui.action_express_uncertainty.triggered.connect(lambda: scoring_uncertainty(ui))
    ui.menu_stages.addAction(ui.action_express_uncertainty)
    
    # Sleep stages menu
    ui.menu_labels = QMenu(ui.menu)
    ui.menu_labels.setObjectName("menu_labels")
    ui.menu.addAction(ui.menu_labels.menuAction())    

    ui.label_box_as = QMenu("Label box as", ui.menu_labels)
    ui.label_box_as.setObjectName("label_box_as")
    ui.menu_labels.addMenu(ui.label_box_as)

    ui.action_artefact = QAction("", ui)
    ui.action_artefact.setObjectName("action_artefact")
    ui.action_artefact.triggered.connect(lambda box_index=0, ui=ui: draw_box(box_index, ui))
    ui.label_box_as.addAction(ui.action_artefact)

    ui.action_F1 = QAction("", ui)
    ui.action_F1.setObjectName("action_F1")
    ui.action_F1.triggered.connect(lambda box_index=1, ui=ui: draw_box(box_index, ui))
    ui.label_box_as.addAction(ui.action_F1)    
    ui.action_F2 = QAction("", ui)
    ui.action_F2.setObjectName("action_F2")
    ui.action_F2.triggered.connect(lambda box_index=2, ui=ui: draw_box(box_index, ui))
    ui.label_box_as.addAction(ui.action_F2)   
    ui.action_F3 = QAction("", ui)
    ui.action_F3.setObjectName("action_F3")
    ui.action_F3.triggered.connect(lambda box_index=3, ui=ui: draw_box(box_index, ui))
    ui.label_box_as.addAction(ui.action_F3)     
    ui.action_F4 = QAction("", ui)
    ui.action_F4.setObjectName("action_F4")
    ui.action_F4.triggered.connect(lambda box_index=4, ui=ui: draw_box(box_index, ui))
    ui.label_box_as.addAction(ui.action_F4)        
    ui.action_F5 = QAction("", ui)
    ui.action_F5.setObjectName("action_F5")
    ui.action_F5.triggered.connect(lambda box_index=5, ui=ui: draw_box(box_index, ui))
    ui.label_box_as.addAction(ui.action_F5)   
    ui.action_F6 = QAction("", ui)
    ui.action_F6.setObjectName("action_F6")
    ui.action_F6.triggered.connect(lambda box_index=6, ui=ui: draw_box(box_index, ui))
    ui.label_box_as.addAction(ui.action_F6)    
    ui.action_F7 = QAction("", ui)
    ui.action_F7.setObjectName("action_F7")
    ui.action_F7.triggered.connect(lambda box_index=7, ui=ui: draw_box(box_index, ui))
    ui.label_box_as.addAction(ui.action_F7)         
    ui.action_F8 = QAction("", ui)
    ui.action_F8.setObjectName("action_F8")
    ui.action_F8.triggered.connect(lambda box_index=8, ui=ui: draw_box(box_index, ui))
    ui.label_box_as.addAction(ui.action_F8)     
    ui.action_F9 = QAction("", ui)
    ui.action_F9.setObjectName("action_F9")
    ui.action_F9.triggered.connect(lambda box_index=9, ui=ui: draw_box(box_index, ui))
    ui.label_box_as.addAction(ui.action_F9)         

    # Utilities menu
    ui.menu_utils = QMenu(ui.menu)
    ui.menu_utils.setObjectName("menu_utils")
    ui.menu.addAction(ui.menu_utils.menuAction())           

    ui.action_zoom = QAction(MainWindow)
    ui.action_zoom.setObjectName("action_zoom")
    ui.action_zoom.triggered.connect(lambda: zoom_on_selected_eeg(ui))
    ui.menu_utils.addAction(ui.action_zoom)

    # Options menu
    ui.menu_config = QMenu(ui.menu)
    ui.menu_config.setObjectName("menu_config")
    ui.menu.addAction(ui.menu_config.menuAction())

    ui.action_config_window = QAction("Open configuration window", MainWindow)
    ui.action_config_window.setObjectName("action_config_window")
    ui.action_config_window.setShortcut("")
    ui.action_config_window.triggered.connect(lambda: open_config_window(ui))
    ui.menu_config.addAction(ui.action_config_window)  

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
