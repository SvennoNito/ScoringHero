# SUMO Model Download Guide

## Quick Start

Run the interactive setup script:

```bash
python setup_sumo.py
```

This will check if you have the model and guide you through download.

## Manual Download Instructions

### Option 1: From SUMO GitHub Repository (Recommended)

1. Clone or download the SUMO repository:
   ```bash
   git clone https://github.com/dslaborg/sumo.git
   ```

2. Find the model file in the repository:
   - Location: `sumo/model/sumo_model.pt` or `sumo/weights/sumo_model.pt`
   - Size: ~100 MB

3. Copy to ScoringHero cache directory:
   
   **Windows:**
   ```powershell
   Copy-Item "path\to\sumo\model\sumo_model.pt" `
     -Destination "$env:LOCALAPPDATA\ScoringHero\ScoringHero\Cache\sumo_model.pt"
   ```
   
   **Linux/macOS:**
   ```bash
   cp sumo/model/sumo_model.pt ~/.cache/ScoringHero/sumo_model.pt
   ```

### Option 2: Verify Model Cache Directory

Check where the model should be placed:

```bash
python -c "
from pathlib import Path
try:
    import appdirs
    cache = Path(appdirs.user_cache_dir('ScoringHero'))
except ImportError:
    import os
    cache = Path(os.path.expanduser('~')) / '.cache' / 'ScoringHero'
    
print(f'Model cache directory: {cache}')
print(f'Expected model path: {cache / \"sumo_model.pt\"}')
cache.mkdir(parents=True, exist_ok=True)
"
```

### Option 3: Download Pre-trained Model from Releases

Check the SUMO GitHub releases page:
- **URL:** https://github.com/dslaborg/sumo/releases
- Look for attachments named `sumo_model.pt` or similar
- Download and place in the cache directory shown above

### Option 4: Using HuggingFace Hub

If the model is published on HuggingFace:

```bash
pip install huggingface-hub

python -c "
from huggingface_hub import hf_hub_download
from pathlib import Path
import os

# Set cache directory
try:
    import appdirs
    cache_dir = Path(appdirs.user_cache_dir('ScoringHero'))
except ImportError:
    cache_dir = Path(os.path.expanduser('~')) / '.cache' / 'ScoringHero'

cache_dir.mkdir(parents=True, exist_ok=True)

# Download
model_path = hf_hub_download(
    repo_id='dslaborg/sumo',
    filename='sumo_model.pt',
    cache_dir=cache_dir
)
print(f'Model downloaded to: {model_path}')
"
```

## Verify Installation

After placing the model file, verify it works:

```bash
python -c "
from scoring.sumo_runner import detect_spindles
import numpy as np

# Create a test signal
test_signal = np.random.randn(30000)  # 300 sec at 100 Hz
sfreq = 100

try:
    events = detect_spindles(test_signal, sfreq)
    print(f'✓ SUMO model loaded successfully')
    print(f'  Found {len(events)} spindle events in test signal')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

## Troubleshooting

### "HTTPError" When Running `setup_sumo.py`

This usually means the GitHub URLs are unavailable. Try manual download (Option 1 above).

### "Model not found" Error in ScoringHero

1. Check the model file exists in the cache directory
2. Verify the file is named exactly: `sumo_model.pt`
3. Check file permissions (should be readable)
4. Restart ScoringHero after placing the file

### Model Cache Directory is Wrong

On Windows, the cache directory sometimes uses a different path. You can manually set the model location:

```python
# In your Python code or notebook
from scoring.sumo_runner import detect_spindles

model_path = r"C:\path\to\sumo_model.pt"
events = detect_spindles(signal, sfreq, model_path=model_path)
```

### Model File Corrupted

If the downloaded file seems corrupted:
1. Delete the incomplete file
2. Re-download from the repository
3. Verify the file size (~100 MB)
4. Check MD5 checksum if provided on GitHub

## Getting Help

- **SUMO GitHub Issues:** https://github.com/dslaborg/sumo/issues
- **Paper:** https://doi.org/10.1038/s41598-022-11210-y
- **ScoringHero Issues:** https://github.com/rkoushik535/ScoringHero/issues

## Alternative: Train Your Own Model

If the pre-trained model is unavailable, you can train SUMO on your own data:

See SUMO documentation: https://github.com/dslaborg/sumo#training
