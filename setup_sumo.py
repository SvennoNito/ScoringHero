#!/usr/bin/env python
"""
Setup script for SUMO spindle detector model.

Downloads the pre-trained SUMO model weights and places them in the correct cache directory.
"""

import sys
import os
from pathlib import Path
import urllib.request
import json


def get_cache_dir():
    """Get the SUMO model cache directory."""
    try:
        import appdirs
        cache_dir = Path(appdirs.user_cache_dir("ScoringHero"))
    except ImportError:
        cache_dir = Path(os.path.expanduser("~")) / ".cache" / "ScoringHero"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_model_path():
    """Get the path where the model should be stored."""
    return get_cache_dir() / "sumo_model.pt"


def check_model_exists():
    """Check if model is already downloaded."""
    model_path = get_model_path()
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✓ SUMO model found at: {model_path}")
        print(f"  Size: {size_mb:.1f} MB")
        return True
    return False


def download_model():
    """Download SUMO model from GitHub."""
    model_path = get_model_path()

    # Try multiple download sources
    urls = [
        "https://github.com/dslaborg/sumo/releases/download/v1.0/sumo_model.pt",
        "https://github.com/dslaborg/sumo/raw/main/model/sumo_model.pt",
        "https://huggingface.co/dslaborg/sumo/resolve/main/sumo_model.pt",
    ]

    print(f"\nDownloading SUMO model to: {model_path}\n")

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Trying: {url}")
        try:
            def progress_hook(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, int(100 * downloaded / total_size))
                    print(f"  Downloaded: {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({percent}%)", end='\r')

            urllib.request.urlretrieve(url, model_path, progress_hook)
            print(f"\n✓ Successfully downloaded model ({model_path.stat().st_size / (1024*1024):.1f} MB)")
            return True
        except Exception as e:
            print(f"  Failed: {type(e).__name__}")
            continue

    return False


def get_github_releases():
    """Check GitHub releases for available models."""
    try:
        url = "https://api.github.com/repos/dslaborg/sumo/releases"
        req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github.v3+json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"Could not check GitHub releases: {e}")
        return None


def manual_download_instructions():
    """Print instructions for manual download."""
    model_path = get_model_path()

    print("\n" + "="*70)
    print("Manual Download Instructions")
    print("="*70)
    print(f"\nModel cache directory: {model_path.parent}\n")
    print("Option 1: Download from GitHub Releases")
    print("  1. Visit: https://github.com/dslaborg/sumo/releases")
    print("  2. Download sumo_model.pt from the latest release")
    print(f"  3. Place the file at: {model_path}\n")

    print("Option 2: Clone the repository")
    print("  git clone https://github.com/dslaborg/sumo.git")
    print(f"  # Copy model/sumo_model.pt to {model_path}\n")

    print("Option 3: Use HuggingFace Hub")
    print("  from huggingface_hub import hf_hub_download")
    print("  hf_hub_download(repo_id='dslaborg/sumo', filename='sumo_model.pt')")
    print("="*70 + "\n")


def main():
    """Main setup routine."""
    print("\n" + "="*70)
    print("SUMO Spindle Detector - Model Setup")
    print("="*70 + "\n")

    # Check if model already exists
    if check_model_exists():
        print("\nNo further action needed. You can use SUMO spindle detection now!")
        return 0

    print("\nSUMO model not found. Attempting download...\n")

    # Try automatic download
    if download_model():
        print("\nSetup complete! You can now use SUMO spindle detection.")
        return 0

    # If automatic download fails, show manual instructions
    print("\nAutomatic download failed. Please download the model manually:\n")
    manual_download_instructions()

    print("After downloading, run this script again to verify installation.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
