#!/usr/bin/env bash

set -euo pipefail

pyinstaller --onefile \
--target-arch=x86_64 \
--icon='icon.icns' \
--paths='./.venv/lib/python3.13/site-packages' scoringhero.py \
--add-data='./.venv/lib/python3.13/site-packages/mne:mne' \
--add-data='./help/images/selection_box.png:help/images' \
--add-data='./themes/light_theme.qss:themes' \
--hidden-import=decorator

