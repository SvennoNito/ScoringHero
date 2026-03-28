@echo off
set UV_PROJECT_ENVIRONMENT=.venv_gssc
uv sync --python 3.13 --extra build-win --extra gssc
uv run --python 3.13 python -m nuitka ^
    --onefile ^
    --jobs=8 ^
    --windows-icon-from-ico=icon.ico ^
    --enable-plugin=pyside6 ^
    --include-module=decorator ^
    --include-module=PySide6.QtOpenGL ^
    --include-module=PySide6.QtOpenGLWidgets ^
    --include-module=widgets.filterWindow ^
    --include-module=widgets.gsscWindow ^
    --include-package=gssc ^
    --include-package=mne ^
    --include-package=torch ^
    --include-data-files=./help/images/selection_box.png=help/images/selection_box.png ^
    --include-data-files=./style/modern_theme.qss=style/modern_theme.qss ^
    --include-data-files=./spectral.txt=spectral.txt ^
    --output-filename=auto-scoringhero_windows.exe ^
    --output-dir=dist ^
    scoringhero.py
