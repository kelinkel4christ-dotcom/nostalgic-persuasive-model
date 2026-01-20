
"""
Script to download trained models from Hugging Face Hub.

Usage:
    This script downloads the 'nostalgic-persuasive-models' repository
    from Hugging Face and places it in the '../models' directory.
    
    You can run this via:
    `pixi run python scripts/download_models.py`
"""

import os
from pathlib import Path
from huggingface_hub import snapshot_download

# Configuration
# Attempt to find the models directory relative to this script
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
# This should match the repo you uploaded to
REPO_ID = "victor-476-/nostalgic-persuasive-models" 

def download_models():
    print(f"Downloading models from Hugging Face: {REPO_ID}...")
    print(f"Target directory: {MODELS_DIR}")
    
    try:
        # snapshot_download downloads the entire repo
        # allow_patterns can be used if we only want specific files
        path = snapshot_download(
            repo_id=REPO_ID,
            repo_type="model",
            local_dir=MODELS_DIR,
            local_dir_use_symlinks=False # Download actual files, not symlinks (easier for windows)
        )
        print(f"✓ Models successfully downloaded to: {path}")
        
    except Exception as e:
        print(f"❌ Error downloading models: {e}")
        # If the user hasn't logged in or it's a private repo
        print("\nIf this is a private repository, make sure you are logged in:")
        print("Run: `huggingface-cli login`")

if __name__ == "__main__":
    download_models()
