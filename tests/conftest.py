"""Headless app fixture: `loaded_ui` boots ScoringHero offscreen with a temp copy of
example_data/example_data.mat, so tests and smoke runs never touch tracked files."""

import os
import shutil

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

EXAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "example_data")


@pytest.fixture
def loaded_ui(tmp_path):
    from PySide6 import QtWidgets

    import scoringhero as sh
    from eeg.load_wrapper import load_wrapper

    for ext in (".mat", ".json", ".config.json"):
        src = os.path.join(EXAMPLE_DIR, "example_data" + ext)
        if os.path.exists(src):
            shutil.copy(src, tmp_path)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    ui = sh.Ui_MainWindow()
    window = sh.MyMainWindow(ui)
    sh.setup_ui(ui, window)
    ui.app_path = str(tmp_path)
    ui.filename = str(tmp_path / "example_data")
    load_wrapper(ui, "eeglab")
    yield ui
    window.close()
    app.processEvents()
