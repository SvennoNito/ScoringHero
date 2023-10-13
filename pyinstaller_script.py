import PyInstaller.__main__
from PyInstaller.utils.hooks import collect_data_files

# Collect data files from 'mne' and 'lspopt' libraries
data_files = collect_data_files('mne') + collect_data_files('lspopt')

# Prepare PyInstaller command
command = [
    '--name=scoringhero',
    '--onefile',
    '--icon=icon.ico',
]

# Add data files
for src, dst in data_files:
    command.append(f'--add-data={src};{dst}')

# Specify the script to be built
command.append('scoringhero.py')

# Run PyInstaller
PyInstaller.__main__.run(command)
