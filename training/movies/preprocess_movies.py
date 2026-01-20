import os
import pandas as pd
import re

# Paths
DATASET_DIR = "../dataset/ml-32m"
MOVIES_FILE = os.path.join(DATASET_DIR, "movies.csv")
OUTPUT_FILE = os.path.join(DATASET_DIR, "enhanced_movies.csv")

def extract_decade(title):
    """Extract decade from movie title (e.g., 'Toy Story (1995)' -> '1990s')."""
    try:
        match = re.search(r'\((\d{4})\)', str(title))
        if match:
            year = int(match.group(1))
            return f"{year // 10 * 10}s"
        return "Unknown"
    except Exception:
        return "Unknown"

def main():
    print("=" * 60)
    print("Movie Preprocessing Pipeline (Simplified)")
    print("=" * 60)
    
    print("\nLoading data...")
    if not os.path.exists(MOVIES_FILE):
        print(f"Error: Movies file not found at {MOVIES_FILE}")
        return

    # Load Movies
    movies = pd.read_csv(MOVIES_FILE, dtype={'movieId': int, 'title': str, 'genres': str})
    print(f"Loaded {len(movies):,} movies")
    
    # 1. Extract Decade
    print("\n[1/1] Extracting decades...")
    movies['decade'] = movies['title'].apply(extract_decade)

    # Save
    print("\n" + "=" * 60)
    print("Sample of enhanced data:")
    print("=" * 60)
    print(movies[['title', 'genres', 'decade']].head(10).to_string())

    print(f"\nSaving enhanced movies to {OUTPUT_FILE}...")
    movies.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\nFinal columns: {list(movies.columns)}")
    print(f"Total movies: {len(movies):,}")
    print("\nDone!")

if __name__ == "__main__":
    main()
