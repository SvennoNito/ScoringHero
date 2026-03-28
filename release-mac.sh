#!/usr/bin/env bash

set -euo pipefail

python -m nuitka \
    --onefile \
    --macos-app-icon=icon.icns \
    --enable-plugin=pyside6 \
    --include-package=mne.io \
    --include-module=decorator \
    --include-module=widgets.filterWindow \
    --include-module=widgets.gsscWindow \
    --include-data-files=./help/images/selection_box.png=help/images/selection_box.png \
    --include-data-files=./style/modern_theme.qss=style/modern_theme.qss \
    --include-data-files=./spectral.txt=spectral.txt \
    --include-distribution-info=scoringhero \
    --output-filename="$FINAL_FILE_NAME" \
    --output-dir=dist \
    scoringhero.py
