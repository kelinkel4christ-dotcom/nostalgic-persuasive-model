
import sys
import os
from pathlib import Path

# Add fastapi-backend to path so we can import the recommender
# Path: training/test/ -> training/ -> project_root/
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "fastapi-backend"
sys.path.append(str(BACKEND_DIR))

from services.song_recommender import SongRecommender

def main():
    print("Initializing Song Recommender...")
    recommender = SongRecommender(
        models_dir=PROJECT_ROOT / "models" / "song_recommender"
    )

    # Test cases: Different decades and genres
    test_queries = [
        "In The End", # Linkin Park (2000s Rock)
        "Bohemian Rhapsody", # Queen (70s Rock) 
        "Toxic" # Britney Spears (2000s Pop)
    ]

    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Testing Query: '{query}'")
        print(f"{'='*50}")

        # 1. Search for the song to get its ID
        search_results = recommender.search_songs(query, limit=1)
        
        if search_results.empty:
            print(f"❌ Song '{query}' not found in database.")
            continue
            
        song_info = search_results.iloc[0]
        song_id = song_info["spotify_id"]
        
        print(f"Found: {song_info['name']} by {song_info['artists']}")
        print(f"Genre: {song_info['genre']} | Year: {song_info['year']}")
        
        # 2. Get Recommendations
        recs = recommender.recommend_by_id(song_id, n_recommendations=5)
        
        print("\n--- Recommendations ---")
        for i, row in recs.iterrows():
            print(f"{i+1}. {row['name']} - {row['artists']}")
            print(f"   (Year: {row['year']} | Genre: {row['genre']} | Sim: {row['similarity']:.3f})")

    recommender.close()

if __name__ == "__main__":
    main()
