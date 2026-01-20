"""
Song Recommender Evaluation Script (Nostalgia-Focused)

This script evaluates the recommender using NOSTALGIA-RELEVANT metrics,
not self-consistency metrics like genre precision or embedding similarity.

Key Principles:
1. Never evaluate on features that are heavily weighted in the embedding
2. Evaluate on what humans remember, not what vectors optimize
3. Use tolerance bands instead of exact similarity

Metrics:
1. Era Recall (±5 years) - HEADLINE METRIC
2. Popularity Drift - Persuasion quality
3. Artist/Scene Continuity - Memory triggers
4. Mood Consistency - Feel, not similarity
5. Duration Familiarity - Era-specific trait
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

# Paths - Support both Docker and local development
if os.path.exists("/models/song_recommender"):
    MODEL_DIR = Path("/models/song_recommender")
    ENV_FILE = Path("/app/.env")
else:
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    MODEL_DIR = PROJECT_ROOT / "models" / "song_recommender"
    ENV_FILE = PROJECT_ROOT / ".env"

RESULTS_FILE = MODEL_DIR / "evaluation_results.json"

load_dotenv(ENV_FILE)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/myapp"
)

# Evaluation parameters
N_QUERIES = 100
N_RECOMMENDATIONS = 10

# Nostalgia tolerance windows
ERA_WINDOW_YEARS = 5  # ±5 years for "same era"
MOOD_TOLERANCE = 0.15  # ±0.15 for valence/energy/danceability
DURATION_TOLERANCE_MS = 15000  # ±15 seconds


# =============================================================================
# Database Functions
# =============================================================================


def connect_database() -> psycopg2.extensions.connection:
    """Connect to PostgreSQL."""
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    print("  Connected!")
    return conn


def get_dataset_stats(conn: psycopg2.extensions.connection) -> dict[str, int]:
    """Get statistics about the song dataset."""
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM song_vectors;")
    total_vectors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM songs;")
    total_songs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT genre) FROM songs;")
    unique_genres = cursor.fetchone()[0]

    cursor.execute("SELECT MIN(year), MAX(year) FROM songs WHERE year IS NOT NULL;")
    year_range = cursor.fetchone()

    cursor.close()

    return {
        "total_vectors": total_vectors,
        "total_songs": total_songs,
        "unique_genres": unique_genres,
        "year_min": year_range[0],
        "year_max": year_range[1],
    }


# =============================================================================
# Nostalgia Evaluation Metrics
# =============================================================================


def evaluate_nostalgia_metrics(
    conn: psycopg2.extensions.connection,
    n_queries: int = 100,
    n_recommendations: int = 10,
) -> dict[str, float]:
    """
    Evaluate the recommender using nostalgia-relevant metrics.

    These metrics answer: "Does this feel like something from that time?"
    NOT: "Are the embeddings close?"

    Args:
        conn: Database connection
        n_queries: Number of test queries
        n_recommendations: Number of recommendations per query

    Returns:
        Dictionary of nostalgia metrics
    """
    print(
        f"\nEvaluating nostalgia metrics ({n_queries} queries, {n_recommendations} recs each)..."
    )

    cursor = conn.cursor()

    # Get random sample of songs for evaluation with all needed fields
    cursor.execute(f"""
        SELECT 
            sv.spotify_id,
            s.year,
            s.popularity,
            s.duration_ms,
            s.valence,
            s.energy,
            s.danceability,
            s.artists,
            s.genre
        FROM song_vectors sv
        JOIN songs s ON sv.spotify_id = s.id
        WHERE s.year IS NOT NULL
          AND s.popularity IS NOT NULL
        ORDER BY RANDOM() 
        LIMIT {n_queries};
    """)
    test_songs = cursor.fetchall()

    if not test_songs:
        print("❌ No songs found in database for evaluation!")
        cursor.close()
        return {}

    # Metric accumulators
    era_recalls: list[float] = []
    popularity_drifts: list[float] = []
    artist_continuities: list[float] = []
    mood_consistencies: list[float] = []
    duration_familiarities: list[float] = []

    for i, row in enumerate(test_songs):
        (
            spotify_id,
            query_year,
            query_popularity,
            query_duration,
            query_valence,
            query_energy,
            query_danceability,
            query_artists,
            query_genre,
        ) = row

        if (i + 1) % 20 == 0:
            print(f"  Processing query {i + 1}/{n_queries}...")

        # Query similar songs with all evaluation fields (with duplicate filtering)
        cursor.execute(
            """
            SELECT year, popularity, duration_ms, valence, energy, danceability, artists, genre
            FROM (
                SELECT DISTINCT ON (LOWER(SPLIT_PART(s.name, ' - ', 1)))
                    s.year,
                    s.popularity,
                    s.duration_ms,
                    s.valence,
                    s.energy,
                    s.danceability,
                    s.artists,
                    s.genre,
                    sv.embedding <=> (SELECT embedding FROM song_vectors WHERE spotify_id = %s) as distance
                FROM song_vectors sv
                JOIN songs s ON sv.spotify_id = s.id
                WHERE sv.spotify_id != %s
                  AND s.year IS NOT NULL
                ORDER BY LOWER(SPLIT_PART(s.name, ' - ', 1)), 
                         sv.embedding <=> (SELECT embedding FROM song_vectors WHERE spotify_id = %s)
            ) sub
            ORDER BY distance
            LIMIT %s;
            """,
            (spotify_id, spotify_id, spotify_id, n_recommendations),
        )
        recommendations = cursor.fetchall()

        if not recommendations:
            continue

        # =================================================================
        # 1. ERA RECALL (HEADLINE METRIC)
        # =================================================================
        # % of recommendations within ±N years of query
        era_matches = sum(
            1
            for r in recommendations
            if r[0] is not None and abs(r[0] - query_year) <= ERA_WINDOW_YEARS
        )
        era_recalls.append(era_matches / len(recommendations))

        # =================================================================
        # 2. POPULARITY DRIFT
        # =================================================================
        # Mean popularity difference (negative = less popular = good for discovery)
        pop_diffs = [
            r[1] - query_popularity for r in recommendations if r[1] is not None
        ]
        if pop_diffs:
            popularity_drifts.append(np.mean(pop_diffs))

        # =================================================================
        # 3. ARTIST/SCENE CONTINUITY
        # =================================================================
        # % of recommendations with overlapping artists
        if query_artists:
            try:
                query_artist_set = (
                    set(query_artists) if isinstance(query_artists, list) else set()
                )
            except (TypeError, ValueError):
                query_artist_set = set()

            artist_matches = 0
            for r in recommendations:
                rec_artists = r[6]
                if rec_artists:
                    try:
                        rec_artist_set = (
                            set(rec_artists) if isinstance(rec_artists, list) else set()
                        )
                        if query_artist_set & rec_artist_set:  # Intersection
                            artist_matches += 1
                    except (TypeError, ValueError):
                        pass
            artist_continuities.append(artist_matches / len(recommendations))

        # =================================================================
        # 4. MOOD CONSISTENCY (tolerance bands, NOT similarity)
        # =================================================================
        # % of recommendations within mood tolerance for valence/energy/danceability
        mood_matches = 0
        for r in recommendations:
            rec_valence, rec_energy, rec_danceability = r[3], r[4], r[5]

            # Check all three mood dimensions
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

            # Require at least 2 of 3 mood dimensions to match
            if sum([valence_ok, energy_ok, danceability_ok]) >= 2:
                mood_matches += 1

        mood_consistencies.append(mood_matches / len(recommendations))

        # =================================================================
        # 5. DURATION FAMILIARITY
        # =================================================================
        # % of recommendations within ±15 seconds of query
        if query_duration:
            duration_matches = sum(
                1
                for r in recommendations
                if r[2] is not None
                and abs(r[2] - query_duration) <= DURATION_TOLERANCE_MS
            )
            duration_familiarities.append(duration_matches / len(recommendations))

    cursor.close()

    # Compute final metrics
    metrics: dict[str, float] = {
        "era_recall": float(np.mean(era_recalls)) if era_recalls else 0.0,
        "popularity_drift_mean": float(np.mean(popularity_drifts))
        if popularity_drifts
        else 0.0,
        "artist_scene_continuity": float(np.mean(artist_continuities))
        if artist_continuities
        else 0.0,
        "mood_consistency": float(np.mean(mood_consistencies))
        if mood_consistencies
        else 0.0,
        "duration_familiarity": float(np.mean(duration_familiarities))
        if duration_familiarities
        else 0.0,
        "n_queries": n_queries,
        "n_recommendations": n_recommendations,
        "era_window_years": ERA_WINDOW_YEARS,
        "mood_tolerance": MOOD_TOLERANCE,
        "duration_tolerance_ms": DURATION_TOLERANCE_MS,
    }

    return metrics


# =============================================================================
# Results Display
# =============================================================================


def print_results(metrics: dict[str, float], stats: dict[str, int]) -> None:
    """Print formatted evaluation results."""
    print("\n" + "=" * 60)
    print("NOSTALGIC RECOMMENDER EVALUATION RESULTS")
    print("=" * 60)

    print(
        f"\n📊 Dataset: {stats['total_songs']:,} songs, {stats['year_min']}-{stats['year_max']}"
    )
    print(
        f"   Queries: {metrics['n_queries']}, Recommendations: {metrics['n_recommendations']}"
    )

    print(f"\n{'Metric':<40} {'Value':>15}")
    print("-" * 60)

    # Era Recall - HEADLINE
    era_pct = metrics["era_recall"] * 100
    era_status = "✅" if era_pct >= 70 else "✓" if era_pct >= 50 else "⚠"
    print(
        f"{era_status} {'Era Recall (±' + str(ERA_WINDOW_YEARS) + ' years)':<38} {era_pct:>14.1f}%"
    )

    # Popularity Drift
    pop_drift = metrics["popularity_drift_mean"]
    pop_status = (
        "✅" if -15 <= pop_drift <= 0 else "✓" if -30 <= pop_drift <= 10 else "⚠"
    )
    print(f"{pop_status} {'Popularity Drift (mean Δ)':<38} {pop_drift:>+14.1f}")

    # Artist/Scene Continuity
    artist_pct = metrics["artist_scene_continuity"] * 100
    artist_status = "✅" if artist_pct >= 30 else "✓" if artist_pct >= 15 else "ℹ️"
    print(f"{artist_status} {'Artist/Scene Continuity':<38} {artist_pct:>14.1f}%")

    # Mood Consistency
    mood_pct = metrics["mood_consistency"] * 100
    mood_status = "✅" if mood_pct >= 60 else "✓" if mood_pct >= 40 else "⚠"
    print(
        f"{mood_status} {'Mood Consistency (±' + str(MOOD_TOLERANCE) + ')':<38} {mood_pct:>14.1f}%"
    )

    # Duration Familiarity
    dur_pct = metrics["duration_familiarity"] * 100
    dur_status = "✅" if dur_pct >= 50 else "✓" if dur_pct >= 30 else "ℹ️"
    print(f"{dur_status} {'Duration Familiarity (±15s)':<38} {dur_pct:>14.1f}%")

    print("-" * 60)

    # Interpretation
    print("\n📋 Interpretation:")
    print(f"   • Era Recall: {era_pct:.0f}% of recommendations are from the same era")

    if pop_drift < 0:
        print(
            f"   • Popularity: Recommends slightly less popular songs (good for discovery)"
        )
    elif pop_drift > 10:
        print(f"   • Popularity: Recommends more popular songs (may feel generic)")
    else:
        print(f"   • Popularity: Similar popularity to query (neutral)")

    print(f"   • Mood: {mood_pct:.0f}% share similar emotional feel")


def save_results(metrics: dict[str, float], stats: dict[str, int]) -> None:
    """Save evaluation results to JSON file."""
    print(f"\nSaving results to {RESULTS_FILE}...")

    results = {
        "metrics": metrics,
        "dataset_stats": stats,
        "evaluation_config": {
            "type": "nostalgia-focused",
            "era_window_years": ERA_WINDOW_YEARS,
            "mood_tolerance": MOOD_TOLERANCE,
            "duration_tolerance_ms": DURATION_TOLERANCE_MS,
            "note": "Metrics evaluate nostalgia relevance, not embedding similarity",
        },
    }

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Results saved to {RESULTS_FILE}")


# =============================================================================
# Main Pipeline
# =============================================================================


def main() -> None:
    """Main evaluation pipeline."""
    print("=" * 60)
    print("SONG RECOMMENDER EVALUATION (Nostalgia-Focused)")
    print("=" * 60 + "\n")

    print("📌 Key principle: Evaluate on what humans remember,")
    print("   not what vectors optimize.\n")

    try:
        # 1. Connect to database
        conn = connect_database()

        # 2. Get dataset statistics
        print("\nGathering dataset statistics...")
        stats = get_dataset_stats(conn)
        print(f"  Song vectors: {stats['total_vectors']:,}")
        print(f"  Total songs: {stats['total_songs']:,}")
        print(f"  Year range: {stats['year_min']}-{stats['year_max']}")

        # 3. Evaluate nostalgia metrics
        metrics = evaluate_nostalgia_metrics(
            conn, n_queries=N_QUERIES, n_recommendations=N_RECOMMENDATIONS
        )

        # 4. Print results
        print_results(metrics, stats)

        # 5. Save results
        save_results(metrics, stats)

        # 6. Close connection
        conn.close()

        print("\n✅ Evaluation complete!")

    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("\nMake sure PostgreSQL is running and DATABASE_URL is set in .env")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
