#!/usr/bin/env bash

set -euo pipefail

python -m nuitka \
    --onefile \
    --lto=no \
    --jobs=8 \
    --macos-app-icon=icon.icns \
    --enable-plugin=pyside6 \
    --include-module=decorator \
    --include-module=PySide6.QtOpenGL \
    --include-module=PySide6.QtOpenGLWidgets \
    --include-module=widgets.filterWindow \
    --include-module=widgets.gsscWindow \
    --include-data-files=./help/images/selection_box.png=help/images/selection_box.png \
    --include-data-files=./style/modern_theme.qss=style/modern_theme.qss \
    --include-data-files=./spectral.txt=spectral.txt \
    --output-filename="$FINAL_FILE_NAME" \
    --output-dir=dist \
    scoringhero.py
