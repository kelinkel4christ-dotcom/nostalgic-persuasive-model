"""
Song Content-Based Filtering Training Script (Nostalgia-Focused)

This script trains a content-based recommender with proper feature separation:
- ANCHOR features: year, genre (define WHERE nostalgia lives)
- STYLE features: audio features (define HOW it feels)
- EVALUATION-ONLY features: popularity, duration, lyrics (NOT in embedding)

Key principles:
1. Don't over-weight features we evaluate on (avoids self-consistency trap)
2. Year is anchor but evaluated loosely (±5 years, not exact match)
3. Popularity/duration/lyrics excluded from embedding but used in evaluation
"""

import ast
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# =============================================================================
# Configuration
# =============================================================================

# Paths - Support both Docker and local development
if os.path.exists("/dataset"):
    # Running in Docker
    DATASET_PATH = Path("/dataset/songs.csv")
    MODELS_DIR = Path("/models/song_recommender")
    ENV_FILE = Path("/app/.env")
else:
    # Local development
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATASET_PATH = (
        PROJECT_ROOT
        / "dataset"
        / "550k Spotify Songs Audio, Lyrics & Genres"
        / "songs.csv"
    )
    MODELS_DIR = PROJECT_ROOT / "models" / "song_recommender"
    ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/myapp"
)

BATCH_SIZE = 1000
RANDOM_SEED = 42
TARGET_DIM = 128

# =============================================================================
# Feature Classification (CRITICAL for proper evaluation)
# =============================================================================

# ANCHOR FEATURES: Define where nostalgia lives
# - Used in embedding with moderate weight
# - Evaluated LOOSELY (era windows, not exact match)
ANCHOR_FEATURES = ["year", "genre"]

# STYLE FEATURES: Define how it feels
# - Used in embedding to capture "sonic vibe"
# - Evaluated via tolerance bands, not exact similarity
STYLE_AUDIO_FEATURES = [
    "danceability",
    "energy",
    "valence",  # Musical positiveness
    "tempo",
    "acousticness",
]

# EMBEDDING-EXCLUDED FEATURES (for evaluation only)
# - NOT used in embedding to avoid evaluation leakage
# - Used in nostalgia-specific metrics
EVALUATION_ONLY_FEATURES = [
    "popularity",  # For persuasion metrics
    "duration_ms",  # For era familiarity
    "lyrics",  # For thematic overlap
    "key",  # Excluded from embedding
    "mode",  # Excluded from embedding
]

# Feature weights for embedding
WEIGHTS = {
    "year": 1.5,  # Important but not over-optimized
    "genre": 1.2,  # Category anchor
    "audio": 1.0,  # Sonic similarity
    "niche_genres": 0.8,  # Scene context
}


# =============================================================================
# Database Functions
# =============================================================================


def connect_database() -> psycopg2.extensions.connection:
    """Connect to PostgreSQL."""
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    print("  Connected!")
    return conn


def get_valid_song_ids(conn: psycopg2.extensions.connection) -> set[str]:
    """Fetch all song IDs that exist in the songs table."""
    print("Fetching valid song IDs from songs table...")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM songs;")
    valid_ids = {row[0] for row in cursor.fetchall()}
    cursor.close()
    print(f"  Found {len(valid_ids):,} songs in database")
    return valid_ids


def insert_vectors_batch(
    conn: psycopg2.extensions.connection,
    df: pd.DataFrame,
    embeddings: np.ndarray,
) -> int:
    """Insert song vectors into the database in batches."""
    cursor = conn.cursor()
    total_inserted = 0

    print(f"Inserting {len(df)} song vectors in batches of {BATCH_SIZE}...")

    for i in range(0, len(df), BATCH_SIZE):
        batch_df = df.iloc[i : i + BATCH_SIZE]
        batch_embeddings = embeddings[i : i + BATCH_SIZE]

        values: list[tuple[str, str]] = []
        for idx, (_, row) in enumerate(batch_df.iterrows()):
            embedding_list = batch_embeddings[idx].tolist()
            embedding_str = f"[{','.join(map(str, embedding_list))}]"
            values.append((str(row["id"]), embedding_str))

        execute_values(
            cursor,
            """
            INSERT INTO song_vectors (spotify_id, embedding)
            VALUES %s
            ON CONFLICT (spotify_id) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                updated_at = NOW();
            """,
            values,
        )
        conn.commit()
        total_inserted += len(values)

        if (i + BATCH_SIZE) % 10000 == 0 or i + BATCH_SIZE >= len(df):
            print(f"  Inserted {total_inserted:,} / {len(df):,} songs...")

    cursor.close()
    return total_inserted


# =============================================================================
# Data Loading and Preprocessing
# =============================================================================


def load_data(filepath: Path) -> pd.DataFrame:
    """Load the songs dataset from CSV."""
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath, low_memory=False)
    print(f"Loaded {len(df):,} songs")
    return df.reset_index(drop=True)


def parse_list_column(value: str) -> list[str]:
    """Safely parse a string representation of a list."""
    if pd.isna(value) or value == "":
        return []
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        return []
    except (ValueError, SyntaxError):
        return []


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess the song data."""
    print("Preprocessing data...")

    # Parse list columns
    df["artists_list"] = df["artists"].apply(parse_list_column)
    df["niche_genres_list"] = df["niche_genres"].apply(parse_list_column)
    df["genres_text"] = df["niche_genres_list"].apply(lambda x: " ".join(x))

    # Fill missing values for audio features
    for feature in STYLE_AUDIO_FEATURES:
        if feature in df.columns:
            df[feature] = df[feature].fillna(df[feature].median())

    # Fill missing anchor features
    df["genre"] = df["genre"].fillna("Unknown")
    df["year"] = df["year"].fillna(df["year"].median())

    print(f"Preprocessing complete. Shape: {df.shape}")
    return df


# =============================================================================
# Feature Engineering (Nostalgia-Focused)
# =============================================================================


def create_feature_vectors(
    df: pd.DataFrame,
    audio_scaler: StandardScaler,
    genre_encoder: OneHotEncoder,
    tfidf_vectorizer: TfidfVectorizer,
    target_dim: int = 128,
    fit: bool = True,
) -> np.ndarray:
    """
    Create feature vectors for content-based filtering.

    IMPORTANT: Only includes anchor and style features.
    Evaluation-only features (popularity, duration, lyrics) are EXCLUDED.
    """
    print("Creating feature vectors...")
    print("  Feature weights:")
    for k, v in WEIGHTS.items():
        print(f"    {k}: {v}x")

    # 1. STYLE: Scale audio features (subset only)
    audio_features = df[STYLE_AUDIO_FEATURES].values
    if fit:
        audio_scaled = audio_scaler.fit_transform(audio_features)
    else:
        audio_scaled = audio_scaler.transform(audio_features)
    print(f"  Audio features shape: {audio_scaled.shape}")

    # 2. ANCHOR: One-hot encode primary genre
    genres = df[["genre"]].values
    if fit:
        genre_encoded = genre_encoder.fit_transform(genres)
    else:
        genre_encoded = genre_encoder.transform(genres)
    print(f"  Genre encoding shape: {genre_encoded.shape}")

    # 3. STYLE: TF-IDF for niche genres (scene context)
    genres_text = df["genres_text"].values
    if fit:
        tfidf_features = tfidf_vectorizer.fit_transform(genres_text).toarray()
    else:
        tfidf_features = tfidf_vectorizer.transform(genres_text).toarray()
    print(f"  TF-IDF features shape: {tfidf_features.shape}")

    # 4. ANCHOR: Normalized year (with moderate weight)
    years = df["year"].values.reshape(-1, 1)
    year_normalized = (years - years.mean()) / (years.std() + 1e-8)

    # 5. Combine with weights (evaluation-only features EXCLUDED)
    combined_features = np.hstack(
        [
            audio_scaled * WEIGHTS["audio"],
            genre_encoded * WEIGHTS["genre"],
            tfidf_features * WEIGHTS["niche_genres"],
            year_normalized * WEIGHTS["year"],
        ]
    )

    print(f"  Combined features shape: {combined_features.shape}")

    # 6. Truncate or pad to target dimension
    current_dim = combined_features.shape[1]
    if current_dim > target_dim:
        vectors = combined_features[:, :target_dim]
        print(f"  Truncated to: {vectors.shape}")
    elif current_dim < target_dim:
        padding = np.zeros((combined_features.shape[0], target_dim - current_dim))
        vectors = np.hstack([combined_features, padding])
        print(f"  Padded to: {vectors.shape}")
    else:
        vectors = combined_features

    # 7. Normalize vectors for cosine similarity
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / (norms + 1e-8)

    return vectors.astype(np.float16)


# =============================================================================
# Model Persistence
# =============================================================================


def save_transformers(
    models_dir: Path,
    audio_scaler: StandardScaler,
    genre_encoder: OneHotEncoder,
    tfidf_vectorizer: TfidfVectorizer,
) -> None:
    """Save fitted transformers to disk."""
    print(f"Saving transformers to {models_dir}...")
    models_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(audio_scaler, models_dir / "audio_scaler.joblib")
    joblib.dump(genre_encoder, models_dir / "genre_encoder.joblib")
    joblib.dump(tfidf_vectorizer, models_dir / "tfidf_vectorizer.joblib")

    # Save training config
    config = {
        "target_dim": TARGET_DIM,
        "style_audio_features": STYLE_AUDIO_FEATURES,
        "weights": WEIGHTS,
        "evaluation_only_features": EVALUATION_ONLY_FEATURES,
        "random_seed": RANDOM_SEED,
    }
    joblib.dump(config, models_dir / "training_config.joblib")

    print("  Saved:")
    print("    - audio_scaler.joblib")
    print("    - genre_encoder.joblib")
    print("    - tfidf_vectorizer.joblib")
    print("    - training_config.joblib")


# =============================================================================
# Main Training Pipeline
# =============================================================================


def main() -> None:
    """Main training pipeline."""
    print("=" * 60)
    print("SONG CONTENT-BASED FILTERING TRAINING (Nostalgia-Focused)")
    print("=" * 60)

    # 1. Connect to database
    conn = connect_database()

    # 2. Load and preprocess data
    df = load_data(DATASET_PATH)

    # 3. Filter to only songs that exist in the songs table
    valid_ids = get_valid_song_ids(conn)
    original_count = len(df)
    df = df[df["id"].isin(valid_ids)].reset_index(drop=True)
    print(
        f"Filtered to {len(df):,} songs (from {original_count:,}) that exist in database"
    )

    if len(df) == 0:
        print("ERROR: No matching songs found in database! Please seed songs first.")
        conn.close()
        return

    df = preprocess_data(df)

    # 4. Initialize transformers
    audio_scaler = StandardScaler()
    genre_encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    tfidf_vectorizer = TfidfVectorizer(max_features=100, stop_words="english")

    # 5. Create feature vectors (WITHOUT evaluation-only features)
    vectors = create_feature_vectors(
        df,
        audio_scaler,
        genre_encoder,
        tfidf_vectorizer,
        target_dim=TARGET_DIM,
        fit=True,
    )

    # 6. Save transformers
    save_transformers(MODELS_DIR, audio_scaler, genre_encoder, tfidf_vectorizer)

    # 7. Insert vectors into database
    total_inserted = insert_vectors_batch(conn, df, vectors)
    print(f"\nTotal songs inserted into pgvector: {total_inserted:,}")

    # 8. Close connection
    conn.close()

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\nVectors stored in PostgreSQL table: song_vectors")
    print(f"Transformers saved to: {MODELS_DIR}")
    print("\nNext step: Run song_evaluation.py for nostalgia metrics")


if __name__ == "__main__":
    main()
