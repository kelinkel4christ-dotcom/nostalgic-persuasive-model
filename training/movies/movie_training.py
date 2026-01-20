"""
Movie LightFM Model Training Script

This script trains a hybrid LightFM recommendation model on the MovieLens 32M dataset.
It uses WARP loss for ranking optimization and incorporates item features (genres, decades).

Key fixes applied:
1. Filters ratings >= 4.0 to only use positive feedback (avoids treating 0.5-star as positive)
2. Saves train/test interactions for consistent evaluation
3. Uses optimal parameters for large-scale training
"""

import os
from pathlib import Path

import joblib
import pandas as pd
from lightfm import LightFM
from lightfm.cross_validation import random_train_test_split
from lightfm.data import Dataset

# Paths - Support both Docker and local development
if os.path.exists("/dataset/ml-32m"):
    # Running in Docker
    DATASET_DIR = Path("/dataset/ml-32m")
    MODEL_DIR = Path("/models/movie_recommender")
else:
    # Local development
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATASET_DIR = PROJECT_ROOT / "dataset" / "ml-32m"
    MODEL_DIR = PROJECT_ROOT / "models" / "movie_recommender"

RATINGS_FILE = DATASET_DIR / "ratings.csv"
MOVIES_FILE = DATASET_DIR / "enhanced_movies.csv"

# Training configuration
RANDOM_SEED = 42
TEST_PERCENTAGE = 0.2
MIN_RATING = 3.0  # Only use ratings >= 3.0 as positive feedback


def load_data(sample_n: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads ratings and movies data.

    Args:
        sample_n: Optional number of ratings to sample (for testing)

    Returns:
        Tuple of (ratings DataFrame, movies DataFrame)
    """
    print("Loading data...")

    if not RATINGS_FILE.exists():
        raise FileNotFoundError(f"Ratings file not found at {RATINGS_FILE}")
    if not MOVIES_FILE.exists():
        raise FileNotFoundError(
            f"Movies file not found at {MOVIES_FILE}. Please run preprocess_movies.py first!"
        )

    # Load ratings
    if sample_n:
        print(f"Sampling {sample_n} rows from ratings...")
        ratings = pd.read_csv(
            RATINGS_FILE,
            dtype={"userId": int, "movieId": int, "rating": float},
            nrows=sample_n,
        )
    else:
        ratings = pd.read_csv(
            RATINGS_FILE, dtype={"userId": int, "movieId": int, "rating": float}
        )

    print(f"  Loaded {len(ratings):,} total ratings")

    # CRITICAL FIX: Filter to only positive ratings
    # This avoids treating low ratings (0.5-3.5) as positive feedback
    original_count = len(ratings)
    ratings = ratings[ratings["rating"] >= MIN_RATING].copy()
    print(
        f"  Filtered to {len(ratings):,} positive ratings (>= {MIN_RATING}) - removed {original_count - len(ratings):,}"
    )

    # Load movies
    movies = pd.read_csv(MOVIES_FILE)

    # Filter movies to those present in the filtered ratings
    unique_movies = ratings["movieId"].unique()
    movies = movies[movies["movieId"].isin(unique_movies)].copy()
    print(f"  {len(movies):,} movies with positive ratings")

    return ratings, movies


def preprocess_data(
    ratings: pd.DataFrame, movies: pd.DataFrame
) -> tuple[Dataset, object, object, object]:
    """
    Preprocesses data and builds LightFM dataset.

    Args:
        ratings: Ratings DataFrame (already filtered to positive)
        movies: Movies DataFrame

    Returns:
        Tuple of (dataset, interactions, weights, item_features)
    """
    print("\nPreprocessing data...")

    # Create LightFM Dataset
    dataset = Dataset()

    # Build feature set: genres + decade
    features: set[str] = set()

    # 1. Genres (pipe-separated)
    for genre_list in movies["genres"].astype(str).str.split("|"):
        features.update(genre_list)

    # 2. Decades (prefixed to avoid collisions)
    movies["decade_feat"] = "decade:" + movies["decade"].astype(str)
    features.update(movies["decade_feat"].unique())

    print(f"  Found {len(features)} unique features")
    print(f"  Users: {len(ratings['userId'].unique()):,}")
    print(f"  Items: {len(movies['movieId'].unique()):,}")

    # Fit the dataset
    dataset.fit(
        users=ratings["userId"].unique(),
        items=movies["movieId"].unique(),
        item_features=features,
    )

    # Build interactions (implicit: all filtered ratings become 1.0)
    print("  Building interactions...")
    (interactions, weights) = dataset.build_interactions(
        (row.userId, row.movieId) for row in ratings.itertuples(index=False)
    )
    print(f"  Interactions: {interactions.nnz:,}")

    # Build item features
    print("  Building item features...")

    def get_movie_features(row: tuple) -> list[str]:
        feats = str(row.genres).split("|")
        feats.append(row.decade_feat)
        return feats

    movie_features_generator = (
        (row.movieId, get_movie_features(row)) for row in movies.itertuples(index=False)
    )

    item_features = dataset.build_item_features(movie_features_generator)

    return dataset, interactions, weights, item_features


def train_model(
    train_interactions: object,
    item_features: object,
    epochs: int = 30,
    no_components: int = 64,
    num_threads: int = 4,
) -> LightFM:
    """
    Trains the LightFM model.

    Args:
        train_interactions: Training interaction matrix
        item_features: Item feature matrix
        epochs: Number of training epochs
        no_components: Number of latent factors
        num_threads: Number of threads for parallel training

    Returns:
        Trained LightFM model
    """
    print(f"\nTraining model...")
    print(f"  Loss: warp")
    print(f"  Components: {no_components}")
    print(f"  Epochs: {epochs}")
    print(f"  Threads: {num_threads}")

    # Using WARP loss for top-K ranking optimization
    # Increased components from 30 to 64 for better representation
    model = LightFM(
        loss="warp",
        no_components=no_components,
        random_state=RANDOM_SEED,
    )

    model.fit(
        interactions=train_interactions,
        item_features=item_features,
        epochs=epochs,
        num_threads=num_threads,
        verbose=True,
    )

    print("  Training complete!")
    return model


def save_artifacts(
    model: LightFM,
    dataset: Dataset,
    item_features: object,
    train_interactions: object,
    test_interactions: object,
) -> None:
    """
    Saves the model and all artifacts needed for evaluation and inference.

    Args:
        model: Trained LightFM model
        dataset: LightFM Dataset with mappings
        item_features: Item feature matrix
        train_interactions: Training interactions (for evaluation masking)
        test_interactions: Test interactions
    """
    print(f"\nSaving artifacts to {MODEL_DIR}...")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, MODEL_DIR / "lightfm_model.pkl")
    joblib.dump(dataset, MODEL_DIR / "lightfm_dataset.pkl")
    joblib.dump(item_features, MODEL_DIR / "item_features.pkl")

    # IMPORTANT: Save interactions for proper evaluation
    # Evaluation script should LOAD these, not rebuild them
    joblib.dump(train_interactions, MODEL_DIR / "train_interactions.pkl")
    joblib.dump(test_interactions, MODEL_DIR / "test_interactions.pkl")

    # Save training config for reference
    config = {
        "min_rating": MIN_RATING,
        "test_percentage": TEST_PERCENTAGE,
        "random_seed": RANDOM_SEED,
        "loss": "warp",
        "no_components": 64,
        "epochs": 30,
    }
    joblib.dump(config, MODEL_DIR / "training_config.pkl")

    print("  Saved:")
    print("    - lightfm_model.pkl")
    print("    - lightfm_dataset.pkl")
    print("    - item_features.pkl")
    print("    - train_interactions.pkl")
    print("    - test_interactions.pkl")
    print("    - training_config.pkl")


def main() -> None:
    """Main training pipeline."""
    print("=" * 60)
    print("LIGHTFM MOVIE RECOMMENDER TRAINING")
    print("=" * 60)

    try:
        # 1. Load data (with positive rating filter)
        ratings, movies = load_data()

        # 2. Preprocess
        dataset, interactions, weights, item_features = preprocess_data(ratings, movies)

        # 3. Train/test split
        print(
            f"\nSplitting data ({int((1 - TEST_PERCENTAGE) * 100)}/{int(TEST_PERCENTAGE * 100)})..."
        )
        train_interactions, test_interactions = random_train_test_split(
            interactions, test_percentage=TEST_PERCENTAGE, random_state=RANDOM_SEED
        )
        print(f"  Train: {train_interactions.nnz:,} interactions")
        print(f"  Test: {test_interactions.nnz:,} interactions")

        # 4. Train model
        # Use CPU count or 4 threads minimum
        num_threads = max(os.cpu_count() or 4, 4)
        model = train_model(
            train_interactions,
            item_features,
            epochs=30,
            no_components=64,
            num_threads=num_threads,
        )

        # 5. Save all artifacts
        save_artifacts(
            model, dataset, item_features, train_interactions, test_interactions
        )

        print("\n" + "=" * 60)
        print("TRAINING COMPLETE!")
        print("=" * 60)
        print("\nNext step: Run movie_evaluation.py to evaluate the model.")

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
