@echo off
uv run python -m nuitka ^
    --onefile ^
    --jobs=4 ^
    --windows-icon-from-ico=icon.ico ^
    --enable-plugin=pyside6 ^
    --include-package=mne.io ^
    --include-module=decorator ^
    --include-data-files=./help/images/selection_box.png=help/images/selection_box.png ^
    --include-data-files=./style/modern_theme.qss=style/modern_theme.qss ^
    --include-data-files=./spectral.txt=spectral.txt ^
    --output-dir=dist ^
    scoringhero.py
