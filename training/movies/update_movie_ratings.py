"""
Compute movie popularity scores from MovieLens ratings.

This script reads the ratings.csv file and computes:
- ratingCount: Number of ratings per movie
- avgRating: Average rating per movie

It then updates the movies table in the database with these values.
"""

import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def compute_movie_ratings(ratings_path: Path) -> pd.DataFrame:
    """
    Compute rating statistics for each movie.

    Args:
        ratings_path: Path to ratings.csv file

    Returns:
        DataFrame with movieId, ratingCount, avgRating
    """
    print(f"Reading ratings from {ratings_path}...")

    # Read ratings in chunks to handle large file (877MB)
    chunks = []
    for chunk in pd.read_csv(ratings_path, chunksize=1_000_000):
        # Group by movieId and compute stats
        grouped = (
            chunk.groupby("movieId")
            .agg(ratingCount=("rating", "count"), ratingSum=("rating", "sum"))
            .reset_index()
        )
        chunks.append(grouped)

    print(f"Processed {len(chunks)} chunks, combining...")

    # Combine all chunks
    combined = pd.concat(chunks)

    # Final aggregation across all chunks
    final = (
        combined.groupby("movieId")
        .agg(ratingCount=("ratingCount", "sum"), ratingSum=("ratingSum", "sum"))
        .reset_index()
    )

    # Calculate average
    final["avgRating"] = final["ratingSum"] / final["ratingCount"]
    final = final.drop(columns=["ratingSum"])

    print(f"Computed stats for {len(final)} movies")
    print(
        f"Rating count range: {final['ratingCount'].min()} - {final['ratingCount'].max()}"
    )
    print(
        f"Average rating range: {final['avgRating'].min():.2f} - {final['avgRating'].max():.2f}"
    )

    return final


def update_database(movie_stats: pd.DataFrame) -> tuple[int, int]:
    """
    Update movies table with rating statistics.

    Args:
        movie_stats: DataFrame with movieId, ratingCount, avgRating

    Returns:
        Tuple of (updated_count, not_found_count)
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    print(f"Connecting to database...")
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    updated = 0
    not_found = 0

    try:
        # Prepare data for bulk update
        print(f"Updating {len(movie_stats)} movies...")

        for i, row in movie_stats.iterrows():
            movie_id = int(row["movieId"])
            rating_count = int(row["ratingCount"])
            avg_rating = float(row["avgRating"])

            cur.execute(
                """
                UPDATE movies
                SET rating_count = %s, avg_rating = %s
                WHERE id = %s
                """,
                (rating_count, avg_rating, movie_id),
            )

            if cur.rowcount > 0:
                updated += 1
            else:
                not_found += 1

            if (i + 1) % 10000 == 0:
                print(
                    f"  Processed {i + 1} movies ({updated} updated, {not_found} not found)"
                )
                conn.commit()

        conn.commit()
        print(f"Done! Updated {updated} movies, {not_found} not found in database")

    finally:
        cur.close()
        conn.close()

    return updated, not_found


def main() -> None:
    """Main entry point."""
    # Path to ratings file
    ratings_path = (
        Path(__file__).parent.parent.parent / "dataset" / "ml-32m" / "ratings.csv"
    )

    if not ratings_path.exists():
        print(f"Error: Ratings file not found at {ratings_path}")
        return

    # Compute stats
    movie_stats = compute_movie_ratings(ratings_path)

    # Update database
    updated, not_found = update_database(movie_stats)

    print(f"\nSummary:")
    print(f"  - Movies with ratings: {len(movie_stats)}")
    print(f"  - Movies updated in DB: {updated}")
    print(f"  - Movies not in DB: {not_found}")


if __name__ == "__main__":
    main()
