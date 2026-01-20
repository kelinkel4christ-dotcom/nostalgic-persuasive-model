import sys
import os
import pandas as pd

# Add parent directory (fastapi-backend) to path so we can import the backend modules
sys.path.insert(0, "..")

from services.song_recommender import SongRecommender


def test_full_recommender():
    print("--- Testing SongRecommender Class ---\n")

    # 1. Initialize
    try:
        recommender = SongRecommender(database_url=os.getenv("DATABASE_URL"))
    except Exception as e:
        print(f"Failed to init: {e}")
        return

    # 2. Simulate User History
    # Let's say user likes "Shape of You" (2017)
    # We want to see if we get some 2017 pop songs AND some random discovery songs
    liked_items = [
        {
            "spotify_id": "7qiZfU4dY1lWllzX7mPBI3",
            "timestamp": "2025-01-01T12:00:00",
        }  # Shape of You (ID from prev test)
    ]

    # "Shape of You" ID might differ in your DB, let's look it up first to be safe
    # Actually, let's just use the recommender to search for it first
    print("Searching for a seed song...")
    search_res = recommender.search_songs("Shape of You", limit=1)
    if not search_res.empty:
        seed_id = search_res.iloc[0]["spotify_id"]
        seed_name = search_res.iloc[0]["name"]
        seed_year = search_res.iloc[0]["year"]
        print(f"  Using Seed: {seed_name} ({seed_year}) [ID: {seed_id}]")
        liked_items = [{"spotify_id": seed_id, "timestamp": None}]
    else:
        print("  Could not find seed song. Using random fallback.")
        liked_items = []

    # 3. Get Recommendations
    print("\nRequesting 10 recommendations (100% Nostalgic 1998-2002)...")

    recommendations = recommender.recommend(
        liked_items=liked_items,
        n_recommendations=10,
        nostalgic_start_year=1998,
        nostalgic_end_year=2002,
    )

    if recommendations.empty:
        print("No recommendations returned.")
        return

    # 4. Analyze Results
    print(f"\nResults ({len(recommendations)}):")
    print(f"{'Title':<30} | {'Year':<4} | {'Strategy':<12} | {'Sim.'}")
    print("-" * 65)

    for _, row in recommendations.iterrows():
        title = row["name"][:27] + ".." if len(row["name"]) > 27 else row["name"]
        year = int(row["year"]) if pd.notna(row["year"]) else "?"
        strategy = row.get("strategy", "unknown")
        sim = f"{row.get('similarity', 0.0):.3f}"

        print(f"{title:<30} | {year:<4} | {strategy:<12} | {sim}")

    # 5. Verify Mix
    strategies = recommendations["strategy"].value_counts()
    print("\nStrategy Distribution:")
    print(strategies)


if __name__ == "__main__":
    test_full_recommender()
