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
from PySide6 import QtWidgets
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import os

from utilities.welcome_banner import print_welcome_banner
from ui.setup_ui import setup_ui
from eeg.load_wrapper import load_wrapper
from widgets import *
from style.appstyler import appstyler
from style.apply_app_theme import apply_app_theme

# Import the actual classes from scoringhero
from scoringhero import GlobalKeyFilter, MyMainWindow, Ui_MainWindow

if __name__ == "__main__":
    print_welcome_banner()
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

    appstyler(app)
    apply_app_theme(MainWindow, app, ui.app_path, "modern_theme.qss")

    MainWindow.activateWindow()
    MainWindow.show()
    sys.exit(app.exec())
