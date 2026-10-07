from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtCore import QRect, QMetaObject
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QMenuBar,
    QMenu,
    QMessageBox,
    QStatusBar,
    )

from .navigation_bar import setup_navigation_bar
from style.icons import icon
from utilities.jump_to_epoch import jump_to_epoch
from widgets import *
from utilities.score_stage import score_stage
from scoring.scoring_export_window import scoring_export_window, export_scoring
from scoring_model.formats import FORMATS
from mouse_click.click_on_hypnogram import click_on_hypnogram
from mouse_click.click_on_spectogram import click_on_spectogram
from mouse_click.move_swa_slider import move_swa_slider
from paint_event.paint_event_handler import paint_event_handler
from utilities.zoom_on_selected_eeg import zoom_on_selected_eeg
from utilities.score_not_sure import score_not_sure
from config.open_config_window import open_config_window
from filter.open_filter_window import open_filter_window
from autoscoring.open_gssc_window import open_gssc_window
from autoscoring.open_nidra_window import open_nidra_window
from event_detection.open_mt_kcd_window import open_mt_kcd_window
from event_detection.open_mt_spindle_window import open_mt_spindle_window
# from event_detection.open_yasa_window import open_yasa_window  # YASA disabled — keep scripts for later
# from event_detection.open_sumo_window import open_sumo_window  # TODO: SUMO needs debugging
from scoring.scoring_import_window import scoring_import_window
from scoring.scoring_import_comparison import scoring_import_comparison, remove_comparison_scoring
from scoring.comparison_stats_window import comparison_stats_window
from eeg.eeg_import_overlay import import_overlay_signal, remove_overlay_signal
from utilities.overlay_state import toggle_show_overlay, set_analysis_source
# from autoscoring.score_yasa import score_yasa
from eeg.eeg_import_window import eeg_import_window
from help.open_help_selection_box import open_help_selection_box
from paint_event.rectangle_events import event_hotkey, erase_events_in_rectangles
from scoring_model.events import N_SLOTS
from export.export_sleep_report import export_sleep_report
from functools import partial

def setup_ui(ui, MainWindow):
    ui.centralwidget = QWidget(MainWindow)
    ui.centralwidget.setObjectName("centralwidget")
    # MainWindow.showMaximized()


    # *** Widgets ***
    # ***************

    # set the grid layout
    layout = QGridLayout()
    ui.centralwidget.setLayout(layout)
    ui.central_layout = layout

    # Build widgets
    ui.SignalWidget = SignalWidget(ui.centralwidget)
    ui.SpectogramWidget = SpectogramWidget(ui.centralwidget, ui.app_path)
    ui.HypnogramWidget = HypnogramWidget(ui.centralwidget)
    ui.HypnogramSlider = HypnogramSlider(ui.centralwidget)
    ui.RectanglePower = RectanglePower(ui.centralwidget)
    ui.PaintEventWidget = PaintEventWidget()
    ui.TFWidget = TFWidget(ui.centralwidget, ui.app_path)

    # Make widgets react to mouse click
    ui.SpectogramWidget.graphics.scene().sigMouseClicked.connect(
        lambda event, ui=ui: click_on_spectogram(event, ui)
    )
    ui.HypnogramWidget.axes.scene().sigMouseClicked.connect(
        lambda event, ui=ui: click_on_hypnogram(event, ui)
    )
    ui.HypnogramSlider.slider.valueChanged.connect(
        lambda value, ui=ui: move_swa_slider(value, ui)
    )
    ui.PaintEventWidget.changesMade.connect(lambda ui=ui: paint_event_handler(ui))

    # Layout
    # Rows 10-77  (68 rows): main EEG signal panel
    layout.addWidget(ui.SignalWidget.axes, 10, 0, 68, 101)
    layout.addWidget(ui.PaintEventWidget, 10, 0, 68, 101)
    # Rows 78-94  (17 rows): time-frequency panel
    layout.addWidget(ui.TFWidget.graphics, 78, 0, 17, 101)
    # Rows 0-9: top panels (unchanged)
    layout.addWidget(ui.SpectogramWidget.graphics, 0, 0, 10, 56)
    layout.addWidget(ui.HypnogramWidget.axes, 0, 56, 10, 30)
    layout.addWidget(ui.HypnogramSlider, 1, 86, 8, 1)
    layout.addWidget(ui.RectanglePower.axes, 0, 87, 10, 13)

    # Status bar (filled by StatusReadout)
    ui.statusbar = QStatusBar(MainWindow)
    ui.statusbar.setObjectName("statusbar")
    ui.StatusReadout = StatusReadout(ui.statusbar)
    ui.EpochReadout = ui.StatusReadout.epoch
    ui.EpochReadout.epochChosen.connect(lambda number, ui=ui: jump_to_epoch(number, ui))
    ui.EpochReadout.editingDone.connect(ui.SignalWidget.axes.setFocus)


    # *** Menu ***
    # ************    

    # menu
    MainWindow.setCentralWidget(ui.centralwidget)
    ui.menu = QMenuBar(MainWindow)
    ui.menu.setGeometry(QRect(0, 0, 800, 22))
    ui.menu.setObjectName("menu")

    # File menu
    ui.menu_file = QMenu("File", ui.menu)
    ui.menu_file.setObjectName("menu_file")
    ui.menu.addAction(ui.menu_file.menuAction())

    # Load EEG submenu
    ui.submenu_load_eeg = QMenu("Load EEG", ui.menu_file)
    ui.submenu_load_eeg.setIcon(icon("folder-open"))
    ui.submenu_load_eeg.setObjectName("submenu_load_eeg")
    ui.menu_file.addMenu(ui.submenu_load_eeg)
    ui.action_load_eeglab = QAction("Load EEGLAB structure (.mat)", ui)
    ui.action_load_eeglab.setObjectName("action_load_eeglab")
    ui.action_load_eeglab.triggered.connect(lambda: eeg_import_window(ui, MainWindow, datatype="eeglab"))
    # ui.action_load_eeglab.setShortcut("Ctrl+O")
    ui.submenu_load_eeg.addAction(ui.action_load_eeglab)
    ui.action_load_r09 = QAction("Load zurich scoring file (.r09)", ui)
    ui.action_load_r09.setObjectName("action_load_r09")
    ui.action_load_r09.triggered.connect(lambda: eeg_import_window(ui, MainWindow, datatype="r09"))
    # ui.action_load_r09.setShortcut("Ctrl+O")
    ui.submenu_load_eeg.addAction(ui.action_load_r09)    
    ui.action_load_edf = QAction("Load EDF file (.edf)", ui)
    ui.action_load_edf.setObjectName("action_load_edf")
    ui.action_load_edf.triggered.connect(lambda: eeg_import_window(ui, MainWindow, datatype="edf"))
    ui.submenu_load_eeg.addAction(ui.action_load_edf)        
    ui.action_load_edf_volt = QAction("Load EDF file (.edf) - scaled from V to \u03BCV", ui)
    ui.action_load_edf_volt.setObjectName("action_load_edf_volt")
    ui.action_load_edf_volt.triggered.connect(lambda: eeg_import_window(ui, MainWindow, datatype="edfvolt"))
    ui.submenu_load_eeg.addAction(ui.action_load_edf_volt)        


    ui.submenu_scoring = QMenu("Load Scoring", ui.menu_file)
    ui.submenu_scoring.setIcon(icon("file-up"))
    ui.submenu_scoring.setObjectName("submenu_scoring")
    ui.menu_file.addMenu(ui.submenu_scoring)
    for fmt in FORMATS.values():
        action = QAction(f"Load {fmt.label}", ui)
        action.setObjectName(f"action_load_{fmt.name}")
        action.triggered.connect(lambda checked=False, name=fmt.name: scoring_import_window(ui, filetype=name))
        setattr(ui, f"action_load_{fmt.name}", action)
        ui.submenu_scoring.addAction(action)
        if fmt.name == "sleeptrip":
            ui.action_load_sleeptrip_events = QAction("Load Sleeptrip Events (_events.csv)", ui)
            ui.action_load_sleeptrip_events.setObjectName("action_load_sleeptrip_events")
            ui.action_load_sleeptrip_events.triggered.connect(lambda: scoring_import_window(ui, filetype="sleeptrip_events"))
            ui.submenu_scoring.addAction(ui.action_load_sleeptrip_events)


    ui.action_save_scoring = QAction(icon("save"), "Save to", MainWindow)
    ui.action_save_scoring.setObjectName("action_save_scoring")
    ui.action_save_scoring.triggered.connect(lambda: scoring_export_window(ui))
    ui.action_save_scoring.setShortcut("Ctrl+S")
    ui.menu_file.addAction(ui.action_save_scoring)

    # Export as submenu
    ui.submenu_export = QMenu("Export as", ui.menu_file)
    ui.submenu_export.setIcon(icon("file-down"))
    ui.submenu_export.setObjectName("submenu_export")
    ui.menu_file.addMenu(ui.submenu_export)
    for fmt in FORMATS.values():
        if fmt.name == "scoringhero":
            continue  # "Save to" writes the ScoringHero file
        action = QAction(fmt.label, ui)
        action.setObjectName(f"action_export_{fmt.name}")
        action.triggered.connect(lambda checked=False, name=fmt.name: export_scoring(ui, name))
        setattr(ui, f"action_export_{fmt.name}", action)
        ui.submenu_export.addAction(action)

    # Export submenu for reports
    ui.submenu_export_reports = QMenu("Export", ui.menu_file)
    ui.submenu_export_reports.setIcon(icon("file-text"))
    ui.submenu_export_reports.setObjectName("submenu_export_reports")
    ui.menu_file.addMenu(ui.submenu_export_reports)
    ui.action_export_sleep_report = QAction("Sleep Report (PDF)", ui)
    ui.action_export_sleep_report.setObjectName("action_export_sleep_report")
    ui.action_export_sleep_report.triggered.connect(lambda: export_sleep_report(ui))
    ui.submenu_export_reports.addAction(ui.action_export_sleep_report)
    ui.action_export_sleep_report.setEnabled(False)

    # Sleep stages menu
    ui.menu_stages = QMenu("Stages", ui.menu)
    ui.menu_stages.setObjectName("menu_stages")
    ui.menu.addAction(ui.menu_stages.menuAction())

    ui.action_None = QAction("None", MainWindow)
    ui.action_None.setObjectName("action_None")
    ui.action_None.triggered.connect(partial(score_stage, None, ui))
    ui.action_None.setShortcut("Delete")
    ui.menu_stages.addAction(ui.action_None)  
    ui.menu_stages.addSeparator()
    ui.action_wake = QAction("Wake",MainWindow)
    ui.action_wake.setObjectName("action_wake")
    ui.action_wake.triggered.connect(partial(score_stage, "Wake", ui))
    ui.action_wake.setShortcut("W")
    ui.menu_stages.addAction(ui.action_wake)
    ui.action_N1 = QAction("N1", MainWindow)
    ui.action_N1.setObjectName("action_N1")
    ui.action_N1.triggered.connect(partial(score_stage, "N1", ui))
    ui.action_N1.setShortcut("1")
    ui.menu_stages.addAction(ui.action_N1)
    ui.action_N2 = QAction("N2", MainWindow)
    ui.action_N2.setObjectName("action_N2")
    ui.action_N2.triggered.connect(partial(score_stage, "N2", ui))
    ui.action_N2.setShortcut("2")
    ui.menu_stages.addAction(ui.action_N2)
    ui.action_N3 = QAction("N3", MainWindow)
    ui.action_N3.setObjectName("action_N3")
    ui.action_N3.triggered.connect(partial(score_stage, "N3", ui))
    ui.action_N3.setShortcut("3")
    ui.menu_stages.addAction(ui.action_N3)
    ui.action_REM = QAction("REM", MainWindow)
    ui.action_REM.setObjectName("action_REM")
    ui.action_REM.triggered.connect(partial(score_stage, "REM", ui))
    ui.action_REM.setShortcut("R")
    ui.menu_stages.addAction(ui.action_REM)
    ui.action_inconclusive = QAction("Inconclusive", MainWindow)
    ui.action_inconclusive.setObjectName("action_inconclusive")
    ui.action_inconclusive.triggered.connect(partial(score_stage, "Inconclusive", ui))
    ui.action_inconclusive.setShortcut("I")    
    ui.menu_stages.addAction(ui.action_inconclusive)  
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
        partial(event_hotkey, slot=0, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_artefact)
    ui.menu_labels.addSeparator()

    ui.action_F1 = QAction("Event 1", MainWindow)
    ui.action_F1.setObjectName("action_F1")
    ui.action_F1.triggered.connect(
        partial(event_hotkey, slot=1, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F1)
    ui.action_F2 = QAction("Event 2", MainWindow)
    ui.action_F2.setObjectName("action_F2")
    ui.action_F2.triggered.connect(
        partial(event_hotkey, slot=2, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F2)
    ui.action_F3 = QAction("Event 3", MainWindow)
    ui.action_F3.setObjectName("action_F3")
    ui.action_F3.triggered.connect(
        partial(event_hotkey, slot=3, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F3)
    ui.action_F4 = QAction("Event 4", MainWindow)
    ui.action_F4.setObjectName("action_F4")
    ui.action_F4.triggered.connect(
        partial(event_hotkey, slot=4, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F4)
    ui.action_F5 = QAction("Event 5", MainWindow)
    ui.action_F5.setObjectName("action_F5")
    ui.action_F5.triggered.connect(
        partial(event_hotkey, slot=5, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F5)
    ui.action_F6 = QAction("Event 6", MainWindow)
    ui.action_F6.setObjectName("action_F6")
    ui.action_F6.triggered.connect(
        partial(event_hotkey, slot=6, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F6)
    ui.action_F7 = QAction("Event 7", MainWindow)
    ui.action_F7.setObjectName("action_F7")
    ui.action_F7.triggered.connect(
        partial(event_hotkey, slot=7, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F7)
    ui.action_F8 = QAction("Event 8", MainWindow)
    ui.action_F8.setObjectName("action_F8")
    ui.action_F8.triggered.connect(
        partial(event_hotkey, slot=8, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F8)
    ui.action_F9 = QAction("Event 9", MainWindow)
    ui.action_F9.setObjectName("action_F9")
    ui.action_F9.triggered.connect(
        partial(event_hotkey, slot=9, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F9)
    ui.action_F10 = QAction("Event 10", MainWindow)
    ui.action_F10.setObjectName("action_F10")
    ui.action_F10.triggered.connect(
        partial(event_hotkey, slot=10, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F10)
    ui.action_F11 = QAction("Event 11", MainWindow)
    ui.action_F11.setObjectName("action_F11")
    ui.action_F11.triggered.connect(
        partial(event_hotkey, slot=11, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F11)
    ui.action_F12 = QAction("Event 12", MainWindow)
    ui.action_F12.setObjectName("action_F12")
    ui.action_F12.triggered.connect(
        partial(event_hotkey, slot=12, ui=ui)
    )
    ui.menu_labels.addAction(ui.action_F12)

    ui.menu_labels.addSeparator()

    ui.action_erase_selection = QAction("Erase events in drawn selection [Backspace]", MainWindow)
    ui.action_erase_selection.setObjectName("action_erase_selection")
    ui.action_erase_selection.triggered.connect(lambda: erase_events_in_rectangles(ui))
    ui.menu_labels.addAction(ui.action_erase_selection)

    ui.action_delete_all_events = QAction("Delete all events", MainWindow)
    ui.action_delete_all_events.setObjectName("action_delete_all_events")
    ui.action_delete_all_events.triggered.connect(lambda: _delete_all_events(ui))
    ui.menu_labels.addAction(ui.action_delete_all_events)


    # Autoscore menu — automatic sleep stage classifiers
    ui.menu_autoscore = QMenu("Autoscore", ui.menu)
    ui.menu_autoscore.setObjectName("menu_autoscore")
    ui.menu.addAction(ui.menu_autoscore.menuAction())

    ui.action_gssc = QAction(icon("bot"), "Greifswald Sleep Stage Classifier (GSSC)", MainWindow)
    ui.action_gssc.setObjectName("action_gssc")
    ui.action_gssc.setShortcut("Ctrl+G")
    ui.action_gssc.setStatusTip("Auto score scalp EEG/EOG with GSSC")
    ui.action_gssc.triggered.connect(lambda: open_gssc_window(ui))
    ui.menu_autoscore.addAction(ui.action_gssc)

    ui.action_nidra = QAction(icon("bot"), "NIDRA (ezscore-f)", MainWindow)
    ui.action_nidra.setObjectName("action_nidra")
    ui.action_nidra.setShortcut("Ctrl+N")
    ui.action_nidra.setStatusTip(
        "Auto score two-channel forehead EEG with NIDRA's ezscore-f ONNX models, "
        "including an artifact class"
    )
    ui.action_nidra.triggered.connect(lambda: open_nidra_window(ui))
    ui.menu_autoscore.addAction(ui.action_nidra)

    # Detectors menu — event detectors
    ui.menu_detectors = QMenu("Detectors", ui.menu)
    ui.menu_detectors.setObjectName("menu_detectors")
    ui.menu.addAction(ui.menu_detectors.menuAction())

    # ui.action_seed = QAction("K-Complex / Spindle Detection (SEED)", MainWindow)
    # ui.action_seed.setObjectName("action_seed")
    # ui.action_seed.triggered.connect(lambda: open_seed_window(ui))
    # ui.menu_detectors.addAction(ui.action_seed)

    ui.action_mt_kcd = QAction(icon("activity"), "K-Complex Detection (MT-KCD)", MainWindow)
    ui.action_mt_kcd.setObjectName("action_mt_kcd")
    ui.action_mt_kcd.setShortcut("Ctrl+K")
    ui.action_mt_kcd.triggered.connect(lambda: open_mt_kcd_window(ui))
    ui.menu_detectors.addAction(ui.action_mt_kcd)

    ui.action_mt_spindle = QAction(icon("activity"), "Spindle Detection (MT-Spindle)", MainWindow)
    ui.action_mt_spindle.setObjectName("action_mt_spindle")
    ui.action_mt_spindle.setShortcut("Ctrl+Shift+S")
    ui.action_mt_spindle.triggered.connect(lambda: open_mt_spindle_window(ui))
    ui.menu_detectors.addAction(ui.action_mt_spindle)

    # YASA spindle detection disabled — scripts kept in scoring/ for later re-enabling
    # ui.action_yasa = QAction("Spindle Detection (YASA)", MainWindow)
    # ui.action_yasa.setShortcut("Ctrl+Shift+Y")
    # ui.action_yasa.triggered.connect(lambda: open_yasa_window(ui))
    # ui.menu_detectors.addAction(ui.action_yasa)

    # TODO: SUMO spindle detection needs debugging - disabled for now
    # ui.action_sumo = QAction("Spindle Detection (SUMO)", MainWindow)
    # ui.action_sumo.setObjectName("action_sumo")
    # ui.action_sumo.setShortcut("Ctrl+Shift+S")
    # ui.action_sumo.triggered.connect(lambda: open_sumo_window(ui))
    # ui.menu_detectors.addAction(ui.action_sumo)

    # Filter menu
    ui.menu_filter = QMenu("Filter", ui.menu)
    ui.menu_filter.setObjectName("menu_filter")
    ui.menu.addAction(ui.menu_filter.menuAction())

    ui.action_filter = QAction(icon("sliders-horizontal"), "Open filter settings", MainWindow)
    ui.action_filter.setObjectName("action_filter")
    ui.action_filter.triggered.connect(lambda: open_filter_window(ui))
    ui.action_filter.setShortcut("Ctrl+F")
    ui.menu_filter.addAction(ui.action_filter)

    # Utilities menu
    ui.menu_utils = QMenu("Utilities", ui.menu)
    ui.menu_utils.setObjectName("menu_utils")
    ui.menu.addAction(ui.menu_utils.menuAction())

    ui.action_zoom = QAction(icon("zoom-in"), "Zoom on selected EEG", MainWindow)
    ui.action_zoom.setObjectName("action_zoom")
    ui.action_zoom.triggered.connect(lambda: zoom_on_selected_eeg(ui))
    ui.action_zoom.setShortcut("Z")
    ui.menu_utils.addAction(ui.action_zoom)

    # Compare menu
    ui.menu_compare = QMenu("Compare", ui.menu)
    ui.menu_compare.setObjectName("menu_compare")
    ui.menu.addAction(ui.menu_compare.menuAction())

    # Compare > Scoring submenu
    ui.menu_compare_scoring = QMenu("Scoring", ui.menu_compare)
    ui.menu_compare_scoring.setObjectName("menu_compare_scoring")
    ui.menu_compare.addMenu(ui.menu_compare_scoring)

    ui.action_import_comparison = QAction("Import scoring for comparison", MainWindow)
    ui.action_import_comparison.setObjectName("action_import_comparison")
    ui.action_import_comparison.triggered.connect(lambda: scoring_import_comparison(ui))
    ui.menu_compare_scoring.addAction(ui.action_import_comparison)

    ui.action_remove_comparison = QAction("Remove comparison scoring", MainWindow)
    ui.action_remove_comparison.setObjectName("action_remove_comparison")
    ui.action_remove_comparison.triggered.connect(lambda: remove_comparison_scoring(ui))
    ui.action_remove_comparison.setEnabled(False)
    ui.menu_compare_scoring.addAction(ui.action_remove_comparison)

    ui.menu_compare_scoring.addSeparator()

    ui.action_comparison_stats = QAction("Show summary statistics", MainWindow)
    ui.action_comparison_stats.setObjectName("action_comparison_stats")
    ui.action_comparison_stats.triggered.connect(lambda: comparison_stats_window(ui))
    ui.action_comparison_stats.setEnabled(False)
    ui.menu_compare_scoring.addAction(ui.action_comparison_stats)

    # Compare > EEG submenu
    ui.menu_compare_eeg = QMenu("EEG", ui.menu_compare)
    ui.menu_compare_eeg.setObjectName("menu_compare_eeg")
    ui.menu_compare.addMenu(ui.menu_compare_eeg)

    ui.submenu_import_overlay = QMenu("Import signal for overlay", ui.menu_compare_eeg)
    ui.submenu_import_overlay.setObjectName("submenu_import_overlay")
    ui.menu_compare_eeg.addMenu(ui.submenu_import_overlay)

    ui.action_import_overlay_eeglab = QAction("Load EEGLAB structure (.mat)", MainWindow)
    ui.action_import_overlay_eeglab.setObjectName("action_import_overlay_eeglab")
    ui.action_import_overlay_eeglab.triggered.connect(lambda: import_overlay_signal(ui, "eeglab"))
    ui.submenu_import_overlay.addAction(ui.action_import_overlay_eeglab)

    ui.action_import_overlay_r09 = QAction("Load zurich scoring file (.r09)", MainWindow)
    ui.action_import_overlay_r09.setObjectName("action_import_overlay_r09")
    ui.action_import_overlay_r09.triggered.connect(lambda: import_overlay_signal(ui, "r09"))
    ui.submenu_import_overlay.addAction(ui.action_import_overlay_r09)

    ui.action_import_overlay_edf = QAction("Load EDF file (.edf)", MainWindow)
    ui.action_import_overlay_edf.setObjectName("action_import_overlay_edf")
    ui.action_import_overlay_edf.triggered.connect(lambda: import_overlay_signal(ui, "edf"))
    ui.submenu_import_overlay.addAction(ui.action_import_overlay_edf)

    ui.action_import_overlay_edf_volt = QAction("Load EDF file (.edf) - scaled from V to μV", MainWindow)
    ui.action_import_overlay_edf_volt.setObjectName("action_import_overlay_edf_volt")
    ui.action_import_overlay_edf_volt.triggered.connect(lambda: import_overlay_signal(ui, "edfvolt"))
    ui.submenu_import_overlay.addAction(ui.action_import_overlay_edf_volt)

    ui.action_remove_overlay = QAction("Remove signal overlay", MainWindow)
    ui.action_remove_overlay.setObjectName("action_remove_overlay")
    ui.action_remove_overlay.triggered.connect(lambda: remove_overlay_signal(ui))
    ui.action_remove_overlay.setEnabled(False)
    ui.menu_compare_eeg.addAction(ui.action_remove_overlay)

    ui.menu_compare_eeg.addSeparator()

    ui.action_show_overlay = QAction("Show overlay", MainWindow)
    ui.action_show_overlay.setObjectName("action_show_overlay")
    ui.action_show_overlay.setCheckable(True)
    ui.action_show_overlay.setEnabled(False)
    ui.action_show_overlay.toggled.connect(lambda checked: toggle_show_overlay(ui, checked))
    ui.menu_compare_eeg.addAction(ui.action_show_overlay)

    ui.menu_compare_eeg.addSeparator()

    # Compare > EEG > Analyze submenu: choose which signal feeds the
    # spectrogram, wavelet (TF) panel, and PSD.
    ui.menu_analyze_source = QMenu("Analyze", ui.menu_compare_eeg)
    ui.menu_analyze_source.setObjectName("menu_analyze_source")
    ui.menu_analyze_source.setEnabled(False)
    ui.menu_compare_eeg.addMenu(ui.menu_analyze_source)

    ui.analyze_source_group = QActionGroup(MainWindow)
    ui.analyze_source_group.setExclusive(True)

    ui.action_analyze_original = QAction("Original signal", MainWindow)
    ui.action_analyze_original.setObjectName("action_analyze_original")
    ui.action_analyze_original.setCheckable(True)
    ui.action_analyze_original.setChecked(True)
    ui.action_analyze_original.toggled.connect(lambda checked: set_analysis_source(ui, "original", checked))
    ui.analyze_source_group.addAction(ui.action_analyze_original)
    ui.menu_analyze_source.addAction(ui.action_analyze_original)

    ui.action_analyze_overlay = QAction("Overlay signal", MainWindow)
    ui.action_analyze_overlay.setObjectName("action_analyze_overlay")
    ui.action_analyze_overlay.setCheckable(True)
    ui.action_analyze_overlay.toggled.connect(lambda checked: set_analysis_source(ui, "overlay", checked))
    ui.analyze_source_group.addAction(ui.action_analyze_overlay)
    ui.menu_analyze_source.addAction(ui.action_analyze_overlay)

    # Options menu
    ui.menu_config = QMenu("Configuration", ui.menu)
    ui.menu_config.setObjectName("menu_config")
    ui.menu.addAction(ui.menu_config.menuAction())

    ui.action_config_window = QAction(icon("settings"), "Open configuration window", MainWindow)
    ui.action_config_window.setObjectName("action_config_window")
    ui.action_config_window.setShortcut("")
    ui.action_config_window.triggered.connect(lambda: open_config_window(ui))
    ui.action_config_window.setShortcut("Ctrl+C")
    ui.menu_config.addAction(ui.action_config_window)

    # Help menu
    ui.menu_help = QMenu("Help", ui.menu)
    ui.menu_help.setObjectName("menu_help")
    ui.menu.addAction(ui.menu_help.menuAction())

    ui.action_help_selection_box = QAction("Signal selection box", MainWindow)
    ui.action_help_selection_box.setObjectName("action_help_selection_box")
    ui.action_help_selection_box.setShortcut("")
    ui.action_help_selection_box.triggered.connect(lambda: open_help_selection_box(ui))
    ui.action_help_selection_box.setShortcut("Ctrl+H")
    ui.menu_help.addAction(ui.action_help_selection_box)    

    # Menus that need a recording start disabled (enable_recording_ui turns them on)
    ui.menu_stages.setEnabled(False)
    ui.menu_labels.setEnabled(False)
    ui.menu_detectors.setEnabled(False)
    ui.menu_filter.setEnabled(False)
    ui.menu_utils.setEnabled(False)
    ui.menu_autoscore.setEnabled(False)
    ui.menu_config.setEnabled(False)

    # Bring together
    MainWindow.setMenuBar(ui.menu)
    MainWindow.setStatusBar(ui.statusbar)
    QMetaObject.connectSlotsByName(MainWindow)

    # *** Setup navigation bar ***
    setup_navigation_bar(ui, MainWindow)

    # Makes GUI listen to key strokes
    MainWindow.keyPressEvent = ui.keyPressEvent


def _delete_all_events(ui):
    msg = QMessageBox()
    msg.setWindowTitle("Delete all events")
    msg.setText(
        "Are you sure you want to delete all events? This is irreversible."
    )
    btn_delete = msg.addButton("Delete all events", QMessageBox.ButtonRole.DestructiveRole)
    btn_epoch = msg.addButton("Delete events on current epoch only", QMessageBox.ButtonRole.DestructiveRole)
    btn_specific = msg.addButton("Delete specific events only", QMessageBox.ButtonRole.ActionRole)
    msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
    msg.exec()

    if msg.clickedButton() is btn_delete:
        def clear_all(events):
            for slot in range(N_SLOTS):
                events.clear(slot)

        ui.edit_events(clear_all)
    elif msg.clickedButton() is btn_epoch:
        _delete_events_in_current_epoch(ui)
    elif msg.clickedButton() is btn_specific:
        open_config_window(ui)
        ui.ConfigurationWindow.tabs.setCurrentIndex(2)


def _delete_events_in_current_epoch(ui):
    length = ui.config[0]["Epoch_length_s"]
    ui.edit_events(lambda events: events.erase([(ui.this_epoch * length, (ui.this_epoch + 1) * length)]))
