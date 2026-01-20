"""
Song Recommender Baseline Evaluation (Audio-Only)

This script evaluates an audio-only baseline by masking non-audio dimensions
in the full embedding and re-normalizing. This isolates the contribution of
sonic features while preserving the same similarity space.

Methodology:
- Zero out non-audio dimensions at query time
- Re-normalize the masked vector
- Run the same ANN search and compute metrics

Embedding Layout (from training):
- Dims 0-4:    Audio features (valence, energy, tempo, danceability, acousticness)
- Dims 5-14:   Genre one-hot encoding
- Dims 15-114: TF-IDF niche genres
- Dim 115:     Year (normalized)
- Dims 116-127: Zero padding
"""

import json
import os
from pathlib import Path

import numpy as np
import psycopg2
from dotenv import load_dotenv

# =============================================================================
# Configuration
# =============================================================================

# Paths
if os.path.exists("/models/song_recommender"):
    MODEL_DIR = Path("/models/song_recommender")
    ENV_FILE = Path("/app/.env")
else:
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    MODEL_DIR = PROJECT_ROOT / "models" / "song_recommender"
    ENV_FILE = PROJECT_ROOT / ".env"

RESULTS_FILE = MODEL_DIR / "baseline_evaluation_results.json"

load_dotenv(ENV_FILE)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/myapp"
)

# Evaluation parameters
N_QUERIES = 100
N_RECOMMENDATIONS = 10

# Embedding dimension layout
AUDIO_DIMS = slice(0, 5)  # Audio features: dims 0-4
GENRE_DIMS = slice(5, 15)  # Genre: dims 5-14
TFIDF_DIMS = slice(15, 115)  # TF-IDF: dims 15-114
YEAR_DIMS = slice(115, 116)  # Year: dim 115

# Nostalgia tolerance windows
ERA_WINDOW_YEARS = 5
MOOD_TOLERANCE = 0.15


# =============================================================================
# Masking Functions
# =============================================================================


def create_audio_only_mask(dim: int = 128) -> np.ndarray:
    """Create a mask that keeps only audio dimensions."""
    mask = np.zeros(dim)
    mask[AUDIO_DIMS] = 1.0
    return mask


def apply_mask_and_normalize(embedding: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Apply mask to embedding and re-normalize."""
    masked = embedding * mask
    norm = np.linalg.norm(masked)
    if norm > 0:
        masked = masked / norm
    return masked


def parse_embedding(embedding_str: str) -> np.ndarray:
    """Parse embedding string from database to numpy array."""
    if isinstance(embedding_str, str):
        return np.array([float(x) for x in embedding_str.strip("[]").split(",")])
    return np.array(embedding_str)


# =============================================================================
# Database Functions
# =============================================================================


def connect_database() -> psycopg2.extensions.connection:
    """Connect to PostgreSQL."""
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    print("  Connected!")
    return conn


# =============================================================================
# Baseline Evaluation
# =============================================================================


def evaluate_audio_only_baseline(
    conn: psycopg2.extensions.connection,
    n_queries: int = 100,
    n_recommendations: int = 10,
) -> dict[str, float]:
    """
    Evaluate audio-only baseline using embedding masking.

    Process:
    1. Get query song and its full embedding
    2. Mask non-audio dimensions, re-normalize
    3. Find nearest neighbors using masked query
    4. Compute nostalgia metrics on results
    """
    print(
        f"\nEvaluating AUDIO-ONLY baseline ({n_queries} queries, {n_recommendations} recs each)..."
    )
    print("  Masking: Keeping only dims 0-4 (audio features)")

    cursor = conn.cursor()
    mask = create_audio_only_mask(128)

    # Get random sample of songs with embeddings
    cursor.execute(f"""
        SELECT 
            sv.spotify_id,
            sv.embedding,
            s.year,
            s.popularity,
            s.valence,
            s.energy,
            s.danceability,
            s.artists,
            s.name
        FROM song_vectors sv
        JOIN songs s ON sv.spotify_id = s.id
        WHERE s.year IS NOT NULL
          AND s.popularity IS NOT NULL
        ORDER BY RANDOM() 
        LIMIT {n_queries};
    """)
    test_songs = cursor.fetchall()

    if not test_songs:
        print("❌ No songs found!")
        cursor.close()
        return {}

    # Metric accumulators
    era_recalls: list[float] = []
    popularity_drifts: list[float] = []
    mood_consistencies: list[float] = []

    for i, row in enumerate(test_songs):
        (
            spotify_id,
            embedding_str,
            query_year,
            query_popularity,
            query_valence,
            query_energy,
            query_danceability,
            query_artists,
            query_name,
        ) = row

        if (i + 1) % 20 == 0:
            print(f"  Processing query {i + 1}/{n_queries}...")

        # Parse and mask embedding
        full_embedding = parse_embedding(embedding_str)
        masked_embedding = apply_mask_and_normalize(full_embedding, mask)
        masked_str = f"[{','.join(map(str, masked_embedding.tolist()))}]"

        # Query using masked embedding, filtering out same-title and variant tracks
        # Extract base name (before any " - " suffix like "Live", "Remaster", etc.)
        base_name = query_name.split(" - ")[0].strip() if query_name else ""

        cursor.execute(
            """
            SELECT year, popularity, valence, energy, danceability, name FROM (
                SELECT DISTINCT ON (LOWER(SPLIT_PART(s.name, ' - ', 1)))
                    s.year,
                    s.popularity,
                    s.valence,
                    s.energy,
                    s.danceability,
                    s.name,
                    sv.embedding <=> %s::vector as distance
                FROM song_vectors sv
                JOIN songs s ON sv.spotify_id = s.id
                WHERE sv.spotify_id != %s
                  AND s.year IS NOT NULL
                  -- Exclude same title matches
                  AND LOWER(s.name) NOT LIKE LOWER(%s)
                  -- Exclude variant tracks of the query song
                  AND LOWER(s.name) NOT LIKE LOWER(%s)
                ORDER BY LOWER(SPLIT_PART(s.name, ' - ', 1)),
                         sv.embedding <=> %s::vector
            ) sub
            ORDER BY distance
            LIMIT %s;
            """,
            (
                masked_str,
                spotify_id,
                f"%{base_name}%",  # Filter songs containing the base name
                f"%{query_name}%" if query_name else "",  # Filter exact name matches
                masked_str,
                n_recommendations,
            ),
        )
        recommendations = cursor.fetchall()

        if not recommendations:
            continue

        # 1. Era Recall
        era_matches = sum(
            1
            for r in recommendations
            if r[0] is not None and abs(r[0] - query_year) <= ERA_WINDOW_YEARS
        )
        era_recalls.append(era_matches / len(recommendations))

        # 2. Popularity Drift
        pop_diffs = [
            r[1] - query_popularity for r in recommendations if r[1] is not None
        ]
        if pop_diffs:
            popularity_drifts.append(np.mean(pop_diffs))

        # 3. Mood Consistency
        mood_matches = 0
        for r in recommendations:
            rec_valence, rec_energy, rec_danceability = r[2], r[3], r[4]

            valence_ok = (
                rec_valence is not None
                and query_valence is not None
                and abs(rec_valence - query_valence) <= MOOD_TOLERANCE
            )
            energy_ok = (
                rec_energy is not None
                and query_energy is not None
                and abs(rec_energy - query_energy) <= MOOD_TOLERANCE
            )
            danceability_ok = (
                rec_danceability is not None
                and query_danceability is not None
                and abs(rec_danceability - query_danceability) <= MOOD_TOLERANCE
            )

            if sum([valence_ok, energy_ok, danceability_ok]) >= 2:
                mood_matches += 1

        mood_consistencies.append(mood_matches / len(recommendations))

    cursor.close()

    metrics: dict[str, float] = {
        "era_recall": float(np.mean(era_recalls)) if era_recalls else 0.0,
        "popularity_drift_mean": float(np.mean(popularity_drifts))
        if popularity_drifts
        else 0.0,
        "mood_consistency": float(np.mean(mood_consistencies))
        if mood_consistencies
        else 0.0,
        "n_queries": n_queries,
        "n_recommendations": n_recommendations,
    }

    return metrics


# =============================================================================
# Results Display
# =============================================================================


def print_comparison(
    baseline_metrics: dict[str, float], full_results_path: Path
) -> None:
    """Print comparison between full model and audio-only baseline."""

    print("\n" + "=" * 70)
    print("AUDIO-ONLY BASELINE COMPARISON")
    print("=" * 70)

    # Load full model results if available
    full_metrics = None
    if full_results_path.exists():
        with open(full_results_path) as f:
            data = json.load(f)
            full_metrics = data.get("metrics", {})

    print(f"\n{'Metric':<35} {'Audio-Only':<15} {'Full Model':<15}")
    print("-" * 70)

    # Era Recall
    baseline_era = baseline_metrics.get("era_recall", 0) * 100
    full_era = full_metrics.get("era_recall", 0) * 100 if full_metrics else 0
    delta_era = baseline_era - full_era if full_metrics else 0
    print(
        f"{'Era Recall (±5 years)':<35} {baseline_era:>13.1f}% {full_era:>13.1f}% ({delta_era:+.1f})"
    )

    # Popularity Drift
    baseline_pop = baseline_metrics.get("popularity_drift_mean", 0)
    full_pop = full_metrics.get("popularity_drift_mean", 0) if full_metrics else 0
    print(f"{'Popularity Drift':<35} {baseline_pop:>+13.1f} {full_pop:>+13.1f}")

    # Mood Consistency
    baseline_mood = baseline_metrics.get("mood_consistency", 0) * 100
    full_mood = full_metrics.get("mood_consistency", 0) * 100 if full_metrics else 0
    delta_mood = baseline_mood - full_mood if full_metrics else 0
    print(
        f"{'Mood Consistency (±0.15)':<35} {baseline_mood:>13.1f}% {full_mood:>13.1f}% ({delta_mood:+.1f})"
    )

    print("-" * 70)

    # Interpretation
    print("\n📋 Interpretation:")
    if full_metrics:
        if full_era > baseline_era + 10:
            print(
                f"  ✅ Year/genre features add +{full_era - baseline_era:.0f}% era recall (significant)"
            )
        else:
            print(f"  ℹ️ Era recall similar—audio features capture temporal patterns")

        if full_mood > baseline_mood + 5:
            print(
                f"  ✅ Full model improves mood consistency by +{full_mood - baseline_mood:.0f}%"
            )
        else:
            print(f"  ℹ️ Audio-only achieves comparable mood matching")


def save_results(metrics: dict[str, float]) -> None:
    """Save baseline evaluation results."""
    print(f"\nSaving results to {RESULTS_FILE}...")

    results = {
        "metrics": metrics,
        "config": {
            "type": "audio-only-baseline",
            "method": "embedding_masking",
            "masked_dims": "0-4 (audio features only)",
            "era_window_years": ERA_WINDOW_YEARS,
            "mood_tolerance": MOOD_TOLERANCE,
        },
    }

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Results saved")


# =============================================================================
# Main
# =============================================================================


def main() -> None:
    """Main evaluation pipeline."""
    print("=" * 70)
    print("SONG RECOMMENDER: AUDIO-ONLY BASELINE EVALUATION")
    print("=" * 70 + "\n")

    print("📌 Method: Mask non-audio dimensions, re-normalize, compare metrics")
    print("   This isolates the contribution of sonic features alone.\n")

    try:
        conn = connect_database()

        # Run baseline evaluation
        baseline_metrics = evaluate_audio_only_baseline(
            conn, n_queries=N_QUERIES, n_recommendations=N_RECOMMENDATIONS
        )

        # Print comparison with full model
        full_results_path = MODEL_DIR / "evaluation_results.json"
        print_comparison(baseline_metrics, full_results_path)

        # Save
        save_results(baseline_metrics)

        conn.close()
        print("\n✅ Baseline evaluation complete!")

    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
