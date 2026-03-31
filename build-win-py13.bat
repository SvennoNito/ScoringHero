@echo off
set UV_PROJECT_ENVIRONMENT=.venv_build
uv sync --python 3.13 --extra build-win
uv run --python 3.13 --extra build-win python -m nuitka ^
    --onefile ^
    --lto=no ^
    --jobs=8 ^
    --windows-icon-from-ico=icon.ico ^
    --enable-plugin=pyside6 ^
    --include-module=decorator ^
    --include-module=PySide6.QtOpenGL ^
    --include-module=PySide6.QtOpenGLWidgets ^
    --include-module=widgets.filterWindow ^
    --include-module=widgets.gsscWindow ^
    --include-data-files=./help/images/selection_box.png=help/images/selection_box.png ^
    --include-data-files=./style/modern_theme.qss=style/modern_theme.qss ^
    --include-data-files=./spectral.txt=spectral.txt ^
    --output-filename=scoringhero_windows.exe ^
    --output-dir=dist ^
    scoringhero.py
