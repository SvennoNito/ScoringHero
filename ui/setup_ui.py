from PySide6.QtGui import QAction
from PySide6.QtCore import QRect, QMetaObject
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QMenuBar,
    QMenu,
    QStatusBar,
    )

from .toolbar import setup_toolbar
from widgets import *
from utilities.timing_decorator import timing_decorator
from utilities.score_stage import score_stage
from scoring.scoring_export_window import scoring_export_window
from mouse_click.click_on_hypnogram import click_on_hypnogram
from mouse_click.click_on_spectogram import click_on_spectogram
from mouse_click.move_spectogram_slider import move_spectogram_slider
from mouse_click.move_swa_slider import move_swa_slider
from paint_event.paint_event_handler import paint_event_handler
from utilities.zoom_on_selected_eeg import zoom_on_selected_eeg
from events.event_handler import event_handler
from utilities.score_not_sure import score_not_sure
from config.open_config_window import open_config_window
from scoring.scoring_import_window import scoring_import_window
from scoring.score_yasa import score_yasa

@timing_decorator
def setup_ui(ui, MainWindow):
    ui.centralwidget = QWidget(MainWindow)
    ui.centralwidget.setObjectName("centralwidget")
    # MainWindow.showMaximized()


    # *** Widgets ***
    # ***************

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
    ui.AnnotationContainer = [
        AnnotationContainer(colorindex=counter, label=f"F{counter}")
        for counter in range(10)
    ]

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
    ui.PaintEventWidget.changesMade.connect(lambda ui=ui: paint_event_handler(ui))

    # Layout
    layout.addWidget(ui.SignalWidget.axes, 10, 0, 85, 101)
    layout.addWidget(ui.PaintEventWidget, 10, 0, 85, 101)
    layout.addWidget(ui.SpectogramWidget.graphics, 0, 0, 10, 55)
    layout.addWidget(ui.SpectogramSlider.slider, 1, 55, 8, 1)
    layout.addWidget(ui.HypnogramWidget.axes, 0, 56, 10, 30)
    layout.addWidget(ui.HypnogramSlider.slider, 1, 86, 8, 1)
    layout.addWidget(ui.RectanglePower.axes, 0, 87, 10, 13)


    # *** Menu ***
    # ************    

    # menu
    MainWindow.setCentralWidget(ui.centralwidget)
    ui.menu = QMenuBar(MainWindow)
    ui.menu.setGeometry(QRect(0, 0, 800, 22))
    ui.menu.setObjectName("menu")
    ui.menu.setStyleSheet("QMenu::item:selected { color: gray; }")

    # File menu
    ui.menu_file = QMenu("File", ui.menu)
    ui.menu_file.setObjectName("menu_file")
    ui.menu.addAction(ui.menu_file.menuAction())

    # Load EEG submenu
    ui.submenu_load_eeg = QMenu("Load EEG", ui.menu_file)
    ui.submenu_load_eeg.setObjectName("submenu_load_eeg")
    ui.menu_file.addMenu(ui.submenu_load_eeg)
    ui.action_load_eeglab = QAction("Load EEGLAB structure (.mat)", ui)
    ui.action_load_eeglab.setObjectName("action_load_eeglab")
    ui.action_load_eeglab.triggered.connect(lambda: ui.load_eeg(datatype="eeglab"))
    # ui.action_load_eeglab.setShortcut("Ctrl+O")
    ui.submenu_load_eeg.addAction(ui.action_load_eeglab)
    ui.action_load_r09 = QAction("Load zurich scoring file (.r09)", ui)
    ui.action_load_r09.setObjectName("action_load_r09")
    ui.action_load_r09.triggered.connect(lambda: ui.load_eeg(datatype="r09"))
    # ui.action_load_r09.setShortcut("Ctrl+O")
    ui.submenu_load_eeg.addAction(ui.action_load_r09)    

    ui.submenu_scoring = QMenu("Load Scoring", ui.menu_file)
    ui.submenu_scoring.setObjectName("submenu_scoring")
    ui.menu_file.addMenu(ui.submenu_scoring)
    ui.action_load_scoringhero = QAction("Load Scoring Hero (.json)", ui)
    ui.action_load_scoringhero.setObjectName("action_load_scoringhero")
    ui.action_load_scoringhero.triggered.connect(lambda: scoring_import_window(ui, filetype="scoringhero"))
    # ui.action_load_scoringhero.setShortcut("Ctrl+Shift+O")
    ui.submenu_scoring.addAction(ui.action_load_scoringhero)
    ui.action_load_vis = QAction("Load Zurich Scoring (.vis)", ui)
    ui.action_load_vis.setObjectName("action_load_vis")
    ui.action_load_vis.triggered.connect(lambda: scoring_import_window(ui, filetype="vis"))
    ui.submenu_scoring.addAction(ui.action_load_vis)

    ui.action_save_scoring = QAction("Save to", MainWindow)
    ui.action_save_scoring.setObjectName("action_save_scoring")
    ui.action_save_scoring.triggered.connect(lambda: scoring_export_window(ui))
    ui.action_save_scoring.setShortcut("Ctrl+S")
    ui.menu_file.addAction(ui.action_save_scoring)

    # Sleep stages menu
    ui.menu_stages = QMenu("Stages", ui.menu)
    ui.menu_stages.setObjectName("menu_stages")
    ui.menu.addAction(ui.menu_stages.menuAction())

    ui.action_wake = QAction("Wake",MainWindow)
    ui.action_wake.setObjectName("action_wake")
    ui.action_wake.triggered.connect(lambda stage="Wake", ui=ui: score_stage(stage, ui))
    ui.action_wake.setShortcut("W")
    ui.menu_stages.addAction(ui.action_wake)
    ui.action_N1 = QAction("N1", MainWindow)
    ui.action_N1.setObjectName("action_N1")
    ui.action_N1.triggered.connect(lambda stage="N1", ui=ui: score_stage(stage, ui))
    ui.action_N1.setShortcut("1")
    ui.menu_stages.addAction(ui.action_N1)
    ui.action_N2 = QAction("N2", MainWindow)
    ui.action_N2.setObjectName("action_N2")
    ui.action_N2.triggered.connect(lambda stage="N2", ui=ui: score_stage(stage, ui))
    ui.action_N2.setShortcut("2")
    ui.menu_stages.addAction(ui.action_N2)
    ui.action_N3 = QAction("N3", MainWindow)
    ui.action_N3.setObjectName("action_N3")
    ui.action_N3.triggered.connect(lambda stage="N3", ui=ui: score_stage(stage, ui))
    ui.action_N3.setShortcut("3")
    ui.menu_stages.addAction(ui.action_N3)
    ui.action_REM = QAction("REM", MainWindow)
    ui.action_REM.setObjectName("action_REM")
    ui.action_REM.triggered.connect(lambda stage="REM", ui=ui: score_stage(stage, ui))
    ui.action_REM.setShortcut("R")
    ui.menu_stages.addAction(ui.action_REM)
    ui.menu_stages.addSeparator()
    ui.action_express_uncertainty = QAction("Not sure", MainWindow)
    ui.action_express_uncertainty.setObjectName("action_express_uncertainty")
    ui.action_express_uncertainty.triggered.connect(lambda: score_not_sure(ui))
    ui.action_express_uncertainty.setShortcut("Q")
    ui.menu_stages.addAction(ui.action_express_uncertainty)

    # Sleep stages menu
    ui.menu_labels = QMenu("Events", ui.menu)
    ui.menu_labels.setObjectName("menu_labels")
    ui.menu.addAction(ui.menu_labels.menuAction())

    # ui.label_box_as = QMenu("Label box as", ui.menu_labels)
    # ui.label_box_as.setObjectName("label_box_as")
    # ui.menu_labels.addMenu(ui.label_box_as)

    ui.action_artefact = QAction("Artefact", MainWindow)
    ui.action_artefact.setObjectName("action_artefact")
    ui.action_artefact.triggered.connect(
        lambda box_index=0, ui=ui: event_handler(box_index, ui)
    )
    ui.action_artefact.setShortcut("A")
    ui.menu_labels.addAction(ui.action_artefact)
    ui.menu_labels.addSeparator()

    ui.action_F1 = QAction("Event 1", MainWindow)
    ui.action_F1.setObjectName("action_F1")
    ui.action_F1.triggered.connect(
        lambda box_index=1, ui=ui: event_handler(box_index, ui)
    )
    ui.action_F1.setShortcut("F1")
    ui.menu_labels.addAction(ui.action_F1)
    ui.action_F2 = QAction("Event 2", MainWindow)
    ui.action_F2.setObjectName("action_F2")
    ui.action_F2.triggered.connect(
        lambda box_index=2, ui=ui: event_handler(box_index, ui)
    )
    ui.action_F2.setShortcut("F2")
    ui.menu_labels.addAction(ui.action_F2)
    ui.action_F3 = QAction("Event 3", MainWindow)
    ui.action_F3.setObjectName("action_F3")
    ui.action_F3.triggered.connect(
        lambda box_index=3, ui=ui: event_handler(box_index, ui)
    )
    ui.action_F3.setShortcut("F3")
    ui.menu_labels.addAction(ui.action_F3)
    ui.action_F4 = QAction("Event 4", MainWindow)
    ui.action_F4.setObjectName("action_F4")
    ui.action_F4.triggered.connect(
        lambda box_index=4, ui=ui: event_handler(box_index, ui)
    )
    ui.action_F4.setShortcut("F4")
    ui.menu_labels.addAction(ui.action_F4)
    ui.action_F5 = QAction("Event 5", MainWindow)
    ui.action_F5.setObjectName("action_F5")
    ui.action_F5.triggered.connect(
        lambda box_index=5, ui=ui: event_handler(box_index, ui)
    )
    ui.action_F5.setShortcut("F5")
    ui.menu_labels.addAction(ui.action_F5)
    ui.action_F6 = QAction("Event 6", MainWindow)
    ui.action_F6.setObjectName("action_F6")
    ui.action_F6.triggered.connect(
        lambda box_index=6, ui=ui: event_handler(box_index, ui)
    )
    ui.action_F6.setShortcut("F6")
    ui.menu_labels.addAction(ui.action_F6)
    ui.action_F7 = QAction("Event 7", MainWindow)
    ui.action_F7.setObjectName("action_F7")
    ui.action_F7.triggered.connect(
        lambda box_index=7, ui=ui: event_handler(box_index, ui)
    )
    ui.action_F7.setShortcut("F7")
    ui.menu_labels.addAction(ui.action_F7)
    ui.action_F8 = QAction("Event 8", MainWindow)
    ui.action_F8.setObjectName("action_F8")
    ui.action_F8.triggered.connect(
        lambda box_index=8, ui=ui: event_handler(box_index, ui)
    )
    ui.action_F8.setShortcut("F8")
    ui.menu_labels.addAction(ui.action_F8)
    ui.action_F9 = QAction("Event 9", MainWindow)
    ui.action_F9.setObjectName("action_F9")
    ui.action_F9.triggered.connect(
        lambda box_index=9, ui=ui: event_handler(box_index, ui)
    )
    ui.action_F9.setShortcut("F9")
    ui.menu_labels.addAction(ui.action_F9)

    # Utilities menu
    ui.menu_utils = QMenu("Utilities", ui.menu)
    ui.menu_utils.setObjectName("menu_utils")
    ui.menu.addAction(ui.menu_utils.menuAction())

    ui.action_yasa = QAction("Let machine sleep score (YASA)", MainWindow)
    ui.action_yasa.setObjectName("action_yasa")
    ui.action_yasa.triggered.connect(lambda: score_yasa(ui))
    ui.menu_utils.addAction(ui.action_yasa)    

    ui.action_zoom = QAction("Zoom on selected EEG", MainWindow)
    ui.action_zoom.setObjectName("action_zoom")
    ui.action_zoom.triggered.connect(lambda: zoom_on_selected_eeg(ui))
    ui.action_zoom.setShortcut("Z")
    ui.menu_utils.addAction(ui.action_zoom)

    # Options menu
    ui.menu_config = QMenu("Configuration", ui.menu)
    ui.menu_config.setObjectName("menu_config")
    ui.menu.addAction(ui.menu_config.menuAction())

    ui.action_config_window = QAction("Open configuration window", MainWindow)
    ui.action_config_window.setObjectName("action_config_window")
    ui.action_config_window.setShortcut("")
    ui.action_config_window.triggered.connect(lambda: open_config_window(ui))
    ui.action_config_window.setShortcut("Ctrl+C")
    ui.menu_config.addAction(ui.action_config_window)

    # Bring together
    MainWindow.setMenuBar(ui.menu)
    ui.statusbar = QStatusBar(MainWindow)
    ui.statusbar.setObjectName("statusbar")
    MainWindow.setStatusBar(ui.statusbar)
    QMetaObject.connectSlotsByName(MainWindow)

    # *** Setup toolbar ***
    setup_toolbar(ui, MainWindow)

    # Makes GUI listen to key strokes
    MainWindow.keyPressEvent = ui.keyPressEvent
