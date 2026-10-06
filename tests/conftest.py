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


@pytest.fixture
def boot_scoring(monkeypatch):
    """Until the app boot builds `ui.scoring` itself, give the session object a settable
    blank one, so the boot's first redraw finds it. Request before `loaded_ui`."""
    from scoring_model.scoring import Scoring

    import scoringhero as sh

    def get(self):
        if "_scoring" not in self.__dict__:
            self._scoring = Scoring(self.numepo, self.config[0]["Epoch_length_s"])
        return self._scoring

    monkeypatch.setattr(sh.Ui_MainWindow, "scoring", property(get, lambda self, v: setattr(self, "_scoring", v)), raising=False)
    monkeypatch.setattr(sh.Ui_MainWindow, "scoring_comparison", None, raising=False)
