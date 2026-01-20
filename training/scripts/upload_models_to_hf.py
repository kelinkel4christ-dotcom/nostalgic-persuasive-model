"""
Script to upload trained models to Hugging Face Hub.

Usage:
    1. Login to Hugging Face: `huggingface-cli login`
    2. Run this script: `pixi run python upload_models_to_hf.py`

This will upload all models from the ../models directory to your Hugging Face account.
"""

from pathlib import Path
from huggingface_hub import HfApi, create_repo
from typing import Literal

# Configuration
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
HF_USERNAME = "YOUR_HF_USERNAME"  # Change this to your Hugging Face username
REPO_NAME = "nostalgic-persuasive-models"  # Name for your HF repository


def upload_folder_to_hf(
    api: HfApi,
    local_folder: Path,
    repo_id: str,
    folder_in_repo: str,
) -> None:
    """Upload a local folder to a specific path in the HF repo."""
    print(f"  Uploading {local_folder.name} to {repo_id}/{folder_in_repo}...")

    try:
        api.delete_folder(path_in_repo=folder_in_repo, repo_id=repo_id)
        print(f"  [OK] Deleted existing {folder_in_repo} folder")
    except Exception:
        pass

    api.upload_folder(
        folder_path=str(local_folder),
        repo_id=repo_id,
        path_in_repo=folder_in_repo,
        commit_message=f"Add {folder_in_repo} model",
    )

    print(f"  [OK] {local_folder.name} uploaded successfully!")


def create_model_card(repo_id: str) -> str:
    """Generate a README.md (model card) for the repository."""
    return f"""---
license: mit
tags:
  - emotion-detection
  - stress-detection
  - movie-recommendation
  - music-recommendation
  - contextual-bandit
  - lightfm
  - roberta
---

# Nostalgic Persuasive Models

This repository contains trained models for the Nostalgic Persuasive Model research project.

## Models Included

### 1. Emotion Model (`emotion_model/`)
- **Architecture**: RoBERTa-based text classification
- **Task**: Multi-class emotion classification from text
- **Format**: Hugging Face Transformers (safetensors)

### 2. Stress Detection Model (`stress_detection_mental_roberta/`)
- **Architecture**: Mental-RoBERTa fine-tuned
- **Task**: Binary stress detection from text
- **Format**: Hugging Face Transformers (safetensors)

### 3. Movie Recommender (`movie_recommender/`)
- **Architecture**: LightFM hybrid collaborative filtering
- **Task**: Movie recommendation based on user preferences
- **Format**: Pickle files (.pkl)
- **Files**:
  - `lightfm_model.pkl` - Trained LightFM model
  - `lightfm_dataset.pkl` - Dataset object for mappings
  - `item_features.pkl` - Item feature matrix

### 4. Song Recommender (`song_recommender/`)
- **Architecture**: Content-based filtering with TF-IDF
- **Task**: Music recommendation based on audio features and lyrics
- **Format**: Joblib files
- **Files**:
  - `audio_scaler.joblib` - StandardScaler for audio features
  - `genre_encoder.joblib` - Label encoder for genres
  - `tfidf_vectorizer.joblib` - TF-IDF vectorizer for lyrics

### 5. Contextual Bandit (`bandit/`)
- **Architecture**: Thompson Sampling contextual bandit
- **Task**: Personalized content selection optimization
- **Format**: Joblib files

## Usage

```python
# For Transformers models (emotion, stress)
from transformers import AutoModelForSequenceClassification, AutoTokenizer

model = AutoModelForSequenceClassification.from_pretrained("{repo_id}/emotion_model")
tokenizer = AutoTokenizer.from_pretrained("{repo_id}/emotion_model")

# For pickle/joblib models
import joblib
from huggingface_hub import hf_hub_download

model_path = hf_hub_download(repo_id="{repo_id}", filename="movie_recommender/lightfm_model.pkl")
model = joblib.load(model_path)
```

## License

MIT License
"""


def main() -> None:
    """Main function to upload all models to Hugging Face Hub."""
    api = HfApi()

    # Get the authenticated user
    user_info = api.whoami()
    username = user_info["name"]
    repo_id = f"{username}/{REPO_NAME}"

    print(f"Authenticated as: {username}")
    print(f"Repository: {repo_id}")
    print(f"Models directory: {MODELS_DIR}")
    print("-" * 50)

    # Create the repository if it doesn't exist
    print(f"\nCreating repository: {repo_id}")
    try:
        create_repo(
            repo_id=repo_id,
            repo_type="model",
            exist_ok=True,
            private=False,  # Set to True if you want a private repo
        )
        print(f"[OK] Repository ready: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"Note: Repository may already exist or error: {e}")

    # Upload README/Model Card
    print("\nUploading model card (README.md)...")
    api.upload_file(
        path_or_fileobj=create_model_card(repo_id).encode(),
        path_in_repo="README.md",
        repo_id=repo_id,
        commit_message="Add model card",
    )
    print("[OK] Model card uploaded!")

    # List of model folders to upload
    model_folders = [
        "emotion_model",
        "stress_detection_mental_roberta",
        "movie_recommender",
        "song_recommender",
        "bandit",
    ]

    # Upload each model folder
    print("\nUploading models...")
    for folder_name in model_folders:
        folder_path = MODELS_DIR / folder_name
        if folder_path.exists():
            upload_folder_to_hf(
                api=api,
                local_folder=folder_path,
                repo_id=repo_id,
                folder_in_repo=folder_name,
            )
        else:
            print(f"  [WARN] Folder not found: {folder_path}")

    print("\n" + "=" * 50)
    print("[OK] All models uploaded successfully!")
    print(f"View your models at: https://huggingface.co/{repo_id}")
    print("=" * 50)


if __name__ == "__main__":
    main()
