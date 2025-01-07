#!/usr/bin/env bash

set -euo pipefail

pyinstaller --onefile \
--target-arch="$TARGET_ARCH" \
--icon='icon.icns' \
--paths="$VENV_PATH/lib/python3.13/site-packages" scoringhero.py \
--add-data="$VENV_PATH/lib/python3.13/site-packages/mne:mne" \
--add-data='./help/images/selection_box.png:help/images' \
--add-data="./style/modern_theme.qss:style" \
--name="$FINAL_FILE_NAME" \
--hidden-import=decorator

