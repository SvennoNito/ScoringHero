"""Headless app fixture: `loaded_ui` boots ScoringHero offscreen with a temp copy of
example_data/example_data.mat, so tests and smoke runs never touch tracked files.

Booting waits for the worker thread that builds the displayed signal and analysis data.
The first boot computes the spectrogram (~2 s) and writes the disk cache; a session
fixture does that once so every test boots from the warm cache (~0.2 s)."""

import os
import shutil
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

EXAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "example_data"
)
EXTENSIONS = (".mat", ".json", ".config.json", ".cache.pkl")


def _copy_example(source_dir, target_dir):
    for ext in EXTENSIONS:
        src = os.path.join(source_dir, "example_data" + ext)
        if os.path.exists(src):
            shutil.copy(src, target_dir)


def _boot(directory):
    """Boot the app on the example recording in `directory`; returns (app, window, ui)."""
    from PySide6 import QtWidgets

    import scoringhero as sh
    from eeg.load_wrapper import load_wrapper

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    ui = sh.Ui_MainWindow()
    window = sh.MyMainWindow(ui)
    sh.setup_ui(ui, window)
    ui.app_path = str(directory)
    ui.filename = os.path.join(str(directory), "example_data")
    load_wrapper(ui, "eeglab")
    # The displayed signal and analysis data are built on a worker thread; wait for it
    # so no thread outlives the test and the hypnogram and spectrogram exist.
    end = time.time() + 120
    while getattr(ui, "_busy_runners", None) and time.time() < end:
        app.processEvents()
        time.sleep(0.01)
    assert not getattr(ui, "_busy_runners", None), "recording did not finish loading"
    return app, window, ui


@pytest.fixture(scope="session")
def warm_example_dir(tmp_path_factory):
    """Example recording with an up-to-date disk cache (built once per session; the
    tracked cache may predate the code, so it is not copied)."""
    from unittest import mock

    import scoringhero as sh

    directory = tmp_path_factory.mktemp("warm_example")
    _copy_example(EXAMPLE_DIR, directory)
    (directory / "example_data.cache.pkl").unlink(missing_ok=True)
    app, window, ui = _boot(directory)
    with mock.patch.object(sh.QMessageBox, "exec", lambda self: sh.QMessageBox.Yes):
        window.close()
    app.processEvents()
    return directory


@pytest.fixture
def loaded_ui(tmp_path, monkeypatch, warm_example_dir):
    import scoringhero as sh

    _copy_example(warm_example_dir, tmp_path)
    app, window, ui = _boot(tmp_path)
    # Closing a partly scored recording asks for confirmation; answer yes instead of blocking.
    monkeypatch.setattr(sh.QMessageBox, "exec", lambda self: sh.QMessageBox.Yes)
    yield ui
    window.close()
    app.processEvents()
