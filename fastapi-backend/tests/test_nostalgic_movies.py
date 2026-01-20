import pandas as pd
import sys
import os

# Add parent directory (fastapi-backend) to path so we can import the backend modules
sys.path.insert(0, "..")
from services.movie_recommender import MovieRecommender


def test_nostalgic_movies():
    print("--- Testing 100% Nostalgic MovieRecommender ---\n")

    try:
        recommender = MovieRecommender(database_url=os.getenv("DATABASE_URL"))
    except Exception as e:
        print(f"Failed to init: {e}")
        return

    # Search for a seed movie
    print("Searching for seed movie (Toy Story)...")
    search_res = recommender.search_movies("Toy Story", limit=1)
    if search_res.empty:
        print("Could not find seed movie.")
        return

    seed = search_res.iloc[0]
    print(f"  Using Seed: {seed['title']} [ID: {seed['movieId']}]")

    liked_items = [{"movieId": int(seed["movieId"]), "timestamp": None}]

    print("\nRequesting 10 recommendations (100% Nostalgic 1990-1999)...")

    recommendations = recommender.recommend(
        liked_items=liked_items,
        n_recommendations=10,
        nostalgic_start_year=1990,
        nostalgic_end_year=1999,
    )

    if recommendations.empty:
        print("No recommendations returned.")
        return

    print(f"\nResults ({len(recommendations)}):")
    print(f"{'Title':<40} | {'Year':<4} | {'Genres':<20} | {'Score'}")
    print("-" * 85)

    for _, row in recommendations.iterrows():
        title = row["title"][:37] + ".." if len(row["title"]) > 37 else row["title"]
        year = int(row["year"]) if pd.notna(row.get("year")) else "?"
        genres = row["genres"][:17] + ".." if len(row["genres"]) > 17 else row["genres"]
        score = f"{row.get('score', 0.0):.2f}"

        print(f"{title:<40} | {year:<4} | {genres:<20} | {score}")

    recommender.close()


if __name__ == "__main__":
    test_nostalgic_movies()
