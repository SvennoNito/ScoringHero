"""
AutoScoringHero: ScoringHero with bundled YASA and GSSC support.

This is a variant of ScoringHero that includes automated scoring and event detection
(YASA spindle detection and GSSC automated sleep staging) pre-configured.

Install with: uv sync --extra auto
Run with: uv run autoscoringhero.py

Required dependencies (auto extra):
  - yasa>=0.6.0       (spindle detection)
  - gssc              (automated sleep staging)
"""

import sys

# Pre-import YASA and GSSC to fail early if they're not installed
try:
    import yasa
    print("[AutoScoringHero] ✓ YASA spindle detection available")
except ImportError as e:
    print(f"[AutoScoringHero] ✗ YASA not installed: {e}")
    print("  Install with: uv pip install yasa")
    sys.exit(1)

try:
    import gssc
    print("[AutoScoringHero] ✓ GSSC auto-scoring available")
except ImportError as e:
    print(f"[AutoScoringHero] ✗ GSSC not installed: {e}")
    print("  Install with: uv pip install gssc")
    sys.exit(1)

# All dependencies available, now run ScoringHero
# Import after dependency checks to fail early
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import scipy.io, os, json, re, h5py, datetime
import numpy as np
from importlib.metadata import version as _pkg_version

from ui.setup_ui import setup_ui
from utilities.timing_decorator import timing_decorator
from utilities.next_epoch import next_epoch
from utilities.prev_epoch import prev_epoch
from eeg.load_wrapper import load_wrapper
from eeg.eeg_import_window import eeg_import_window
from widgets import *
from signal_processing.times_vector import times_vector
from events.draw_event_in_this_epoch import draw_event_in_this_epoch
from events.event_handler import event_handler
from events.erase_events_in_rectangles import erase_events_in_rectangles
from cache.load_cache import load_cache
from scoring.write_scoring import write_scoring
from style.appstyler import appstyler
from style.apply_app_theme import apply_app_theme

# Import the actual classes from scoringhero
from scoringhero import GlobalKeyFilter, MyMainWindow, Ui_MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    ui = Ui_MainWindow()
    MainWindow = MyMainWindow(ui)

    key_filter = GlobalKeyFilter(ui, app)
    app.installEventFilter(key_filter)

    setup_ui(ui, MainWindow)
    if ui.devmode == 1:
        name_of_eegfile = os.path.join(ui.default_data_path, "example_data.mat")
        ui.filename, suffix = os.path.splitext(name_of_eegfile)
        MainWindow.setWindowTitle(f"Scoring Hero v.{ui.version[0]}.{ui.version[1]}.{ui.version[2]} ({os.path.basename(name_of_eegfile)})")
        load_wrapper(ui, 'eeglab')

        # Enable menus, toolbar, and sliders
        ui.menu_stages.setEnabled(True)
        ui.menu_labels.setEnabled(True)
        ui.menu_utils.setEnabled(True)
        ui.menu_config.setEnabled(True)
        ui.toolbar_jump_to_epoch.setEnabled(True)
        ui.tool_nextunscored.setEnabled(True)
        ui.tool_nextuncertain.setEnabled(True)
        ui.tool_nexttransition.setEnabled(True)
        ui.tool_nextevent.setEnabled(True)
        ui.tool_nexthuman.setEnabled(True)
        ui.HypnogramSlider.enable_slider()

    appstyler(app)
    apply_app_theme(MainWindow, app, ui.app_path, "modern_theme.qss")

    MainWindow.activateWindow()
    MainWindow.show()
    sys.exit(app.exec())
