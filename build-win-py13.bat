@echo off
set UV_PROJECT_ENVIRONMENT=.venv_build
uv run --python 3.13 --extra build-win python -m nuitka ^
    --onefile ^
    --jobs=8 ^
    --windows-icon-from-ico=icon.ico ^
    --enable-plugin=pyside6 ^
    --include-module=decorator ^
    --include-module=PySide6.QtOpenGL ^
    --include-module=PySide6.QtOpenGLWidgets ^
    --include-data-files=./help/images/selection_box.png=help/images/selection_box.png ^
    --include-data-files=./style/modern_theme.qss=style/modern_theme.qss ^
    --include-data-files=./spectral.txt=spectral.txt ^
    --output-dir=dist ^
    scoringhero.py
