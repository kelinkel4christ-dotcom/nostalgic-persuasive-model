"""
Movie Recommendation API - Cold Start User Support

This module provides movie recommendations for new users who are not in the
original training dataset. It uses LightFM's user folding technique to generate
recommendations based on a list of movies the user has liked.

Uses PostgreSQL backend for movie metadata.

Usage:
    from recommend_movies import MovieRecommender

    recommender = MovieRecommender()
    recommendations = recommender.recommend(
        liked_movie_ids=[1, 2, 3],  # MovieLens movieIds
        n_recommendations=10
    )
"""

import json
import os
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Paths (services/ -> fastapi-backend/ -> project_root/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load environment variables
load_dotenv(ENV_FILE)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/myapp"
)


class MovieRecommender:
    """
    Movie recommender using LightFM with cold-start user support.

    This class loads the trained LightFM model and provides recommendations
    for new users based on movies they've liked (user folding).

    Uses PostgreSQL for movie metadata storage.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
    ) -> None:
        """
        Initialize the recommender by loading the trained model and connecting to database.
        Requires HF_REPO_ID environment variable.

        Args:
            database_url: PostgreSQL connection string.
        """
        self.database_url = database_url or DATABASE_URL

        # Database connection (no longer persistent)
        # self._conn: Optional[psycopg2.extensions.connection] = None

        # Mappings
        self._user_id_map = {}
        self._item_id_map = {}
        self._old_movie_cache = {"internal_ids": [], "movie_ids": [], "metadata": {}}

        # Load model artifacts
        repo_id = os.getenv("HF_REPO_ID")

        if not repo_id:
            raise ValueError("HF_REPO_ID environment variable must be set")

        print(f"Loading LightFM model from Hugging Face Hub: {repo_id}...")
        try:
            from huggingface_hub import hf_hub_download

            # Download and load lightfm_model.pkl
            model_path = hf_hub_download(
                repo_id=repo_id, filename="movie_recommender/lightfm_model.pkl"
            )
            self.model = joblib.load(model_path)

            # Download and load lightfm_dataset.pkl
            dataset_path = hf_hub_download(
                repo_id=repo_id, filename="movie_recommender/lightfm_dataset.pkl"
            )
            self.dataset = joblib.load(dataset_path)

            # Download and load item_features.pkl
            features_path = hf_hub_download(
                repo_id=repo_id, filename="movie_recommender/item_features.pkl"
            )
            self.item_features = joblib.load(features_path)

            print("✓ Models downloaded and loaded from HF Hub")

            # Initialize mappings and cache
            (
                self._user_id_map,
                self._user_feature_map,
                self._item_id_map,
                self._item_feature_map,
            ) = self.dataset.mapping()
            # Reverse mapping
            self._internal_to_movie = {v: k for k, v in self._item_id_map.items()}
            self.n_items = len(self._item_id_map)

            # Build cache
            self._old_movie_cache = self._build_old_movie_cache()

        except Exception as e:
            print(f"⚠ Failed to load from HF Hub: {e}")
            raise

    def _get_connection(self) -> psycopg2.extensions.connection:
        """Get a new database connection."""
        return psycopg2.connect(self.database_url)

    def close(self) -> None:
        """Close the database connection (No-op as we use per-request connections)."""
        pass

    def _build_old_movie_cache(self, min_years_old: int = 10) -> dict:
        """
        Pre-compute cache of old movies for fast filtering.
        Called once at startup.

        Returns:
            Dict with 'internal_ids' (numpy array), 'movie_ids', and 'metadata'
        """
        import datetime

        max_year = datetime.datetime.now().year - min_years_old

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, title, year, genres, rating_count
                FROM movies
                WHERE year IS NOT NULL AND year <= %s;
            """,
                (max_year,),
            )

            rows = cursor.fetchall()
            cursor.close()

            # Build cache with only movies that exist in our model
            internal_ids = []
            movie_ids = []
            metadata = {}  # movie_id -> (title, year, genres, rating_count)

            for row in rows:
                movie_id = row[0]
                if movie_id in self._item_id_map:
                    internal_id = self._item_id_map[movie_id]
                    internal_ids.append(internal_id)
                    movie_ids.append(movie_id)
                    metadata[movie_id] = {
                        "title": row[1],
                        "year": row[2],
                        "genres": row[3],
                        "rating_count": row[4] or 0,
                    }

            return {
                "internal_ids": np.array(internal_ids, dtype=np.int32),
                "movie_ids": np.array(movie_ids, dtype=np.int32),
                "metadata": metadata,
            }
        finally:
            conn.close()

    def _format_genres(self, genres_json: list[str] | str | None) -> str:
        """
        Format genres from JSON array to pipe-separated string.

        Args:
            genres_json: JSON array of genres or already formatted string

        Returns:
            Pipe-separated genres string
        """
        if genres_json is None:
            return ""
        if isinstance(genres_json, str):
            try:
                genres_list = json.loads(genres_json)
                return "|".join(genres_list) if genres_list else ""
            except json.JSONDecodeError:
                return genres_json
        if isinstance(genres_json, list):
            return "|".join(genres_json)
        return str(genres_json)

    def _calculate_decade(self, year: int | None) -> str:
        """
        Calculate decade from year.

        Args:
            year: Release year

        Returns:
            Decade string (e.g., "1990s")
        """
        if year is None:
            return "Unknown"
        decade = (year // 10) * 10
        return f"{decade}s"

    def _get_item_internal_ids(self, movie_ids: list[int]) -> list[int]:
        """
        Convert external movieIds to internal item indices.

        Args:
            movie_ids: List of MovieLens movieIds

        Returns:
            List of internal item indices (skipping unknown movies)
        """
        internal_ids = []
        for mid in movie_ids:
            if mid in self._item_id_map:
                internal_ids.append(self._item_id_map[mid])
            else:
                print(f"Warning: movieId {mid} not found in training data, skipping.")
        return internal_ids

    def _build_user_features_from_items(self, internal_props: list[dict]) -> np.ndarray:
        """
        Build a pseudo-user feature vector based on liked items with recency weighting.

        Args:
            internal_props: List of dicts {internal_id, timestamp}

        Returns:
            User embedding vector
        """
        if not internal_props:
            raise ValueError("No valid movie IDs provided for recommendations.")

        import datetime

        now = datetime.datetime.now()

        # Get item representations from the model
        item_biases, item_embeddings = self.model.get_item_representations(
            features=self.item_features
        )

        # Calculate weights
        embeddings = []
        weights = []

        for prop in internal_props:
            idx = prop["internal_id"]
            embeddings.append(item_embeddings[idx])

            timestamp = prop.get("timestamp")
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.datetime.fromisoformat(timestamp)
                    except ValueError:
                        timestamp = now

                delta = now - timestamp
                days = max(0, delta.days)
                # Formula: 1 / (1 + 0.1 * days)
                weight = 1.0 / (1.0 + 0.1 * days)
                weight = max(weight, 0.2)  # Safety floor
            else:
                weight = 0.5

            weights.append(weight)

        # Weighted Average
        user_embedding = np.average(embeddings, axis=0, weights=weights)

        return user_embedding

    def recommend(
        self,
        liked_items: list[dict],
        n_recommendations: int = 10,
        exclude_liked: bool = True,
        min_years_old: int = 10,
    ) -> pd.DataFrame:
        """
        Generate movie recommendations for a new user based on movies they've liked.

        Args:
            liked_items: List of dicts {"movieId": int, "timestamp": datetime}
            n_recommendations: Number of recommendations to return
            exclude_liked: Whether to exclude liked movies from recommendations
            min_years_old: Minimum age of content in years (default 10 for nostalgia)

        Returns:
            DataFrame with recommended movies and their scores
        """
        # Convert to internal IDs
        internal_props = []
        for item in liked_items:
            mid = item["movieId"]
            if mid in self._item_id_map:
                internal_props.append(
                    {
                        "internal_id": self._item_id_map[mid],
                        "timestamp": item.get("timestamp"),
                    }
                )
            else:
                print(f"Warning: movieId {mid} not found in training data, skipping.")

        if not internal_props:
            # Fallback if no valid history, return some popular movies
            return self._get_popular_fallback(
                n_recommendations, min_years_old=min_years_old
            )

        # Build user embedding from liked items (weighted)
        user_embedding = self._build_user_features_from_items(internal_props)

        # Get item representations
        item_biases, item_embeddings = self.model.get_item_representations(
            features=self.item_features
        )

        # Calculate scores for all items using dot product (vectorized)
        all_scores = item_embeddings.dot(user_embedding) + item_biases

        # Create exclusion set for liked items
        excluded_internal_ids = (
            {prop["internal_id"] for prop in internal_props} if exclude_liked else set()
        )

        # OPTIMIZED: Use pre-computed cache for old movies
        cache = self._old_movie_cache
        internal_ids = cache["internal_ids"]
        movie_ids = cache["movie_ids"]
        metadata = cache["metadata"]

        # Vectorized score lookup using NumPy fancy indexing
        old_scores = all_scores[internal_ids]

        # Create mask for non-excluded items
        if excluded_internal_ids:
            exclude_mask = np.array(
                [iid not in excluded_internal_ids for iid in internal_ids]
            )
            old_scores = np.where(exclude_mask, old_scores, -np.inf)

        # Get top N indices using partial sort (argsort is fast for this)
        top_indices = np.argsort(-old_scores)[:n_recommendations]

        # Build results
        results = []
        for idx in top_indices:
            mid = int(movie_ids[idx])
            score = float(old_scores[idx])
            if score > -np.inf:
                meta = metadata[mid]
                results.append(
                    {
                        "movieId": mid,
                        "title": meta["title"],
                        "year": meta["year"],
                        "genres": self._format_genres(meta["genres"]),
                        "rating_count": meta["rating_count"],
                        "decade": self._calculate_decade(meta["year"]),
                        "score": score,
                    }
                )

        return pd.DataFrame(results)

    def _get_popular_fallback(self, n: int, min_years_old: int = 10) -> pd.DataFrame:
        """Fallback for empty history."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Calculate max year
            import datetime

            current_year = datetime.date.today().year
            max_year = current_year - min_years_old

            # Get random popular movies that meet the criteria
            # This is a bit inefficient (fetching all IDs then sampling), but safe for now
            # Ideally we'd have a 'popular_old_movies' table or view
            cursor.execute(
                """
                SELECT id FROM movies 
                WHERE year <= %s 
                ORDER BY rating_count DESC 
                LIMIT 500
            """,
                (max_year,),
            )

            rows = cursor.fetchall()

            if not rows:
                cursor.close()
                return pd.DataFrame()

            # Sample from top 500
            import random

            all_ids = [r[0] for r in rows]
            selected_ids = random.sample(all_ids, min(n, len(all_ids)))

            placeholders = ",".join(["%s"] * len(selected_ids))
            cursor.execute(
                f"SELECT id, title, year, genres FROM movies WHERE id IN ({placeholders})",
                selected_ids,
            )
            rows = cursor.fetchall()
            cursor.close()

            results = []
            for row in rows:
                results.append(
                    {
                        "movieId": row[0],
                        "title": row[1],
                        "genres": self._format_genres(row[3]),
                        "decade": self._calculate_decade(row[2]),
                        "score": 0.0,
                    }
                )
            return pd.DataFrame(results)
        finally:
            conn.close()

    def get_random_recommendations(
        self, n: int = 10, min_years_old: int = 0
    ) -> pd.DataFrame:
        """
        Get random movie recommendations.

        Args:
            n: Number of recommendations
            min_years_old: Minimum age of movie in years

        Returns:
            DataFrame with random movies
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Calculate max year
            import datetime

            current_year = datetime.date.today().year
            max_year = current_year - min_years_old

            cursor.execute(
                """
                SELECT id, title, year, genres, rating_count
                FROM movies
                WHERE year <= %s
                ORDER BY RANDOM()
                LIMIT %s;
            """,
                (max_year, n),
            )

            rows = cursor.fetchall()
            cursor.close()

            results = []
            for row in rows:
                results.append(
                    {
                        "movieId": row[0],
                        "title": row[1],
                        "year": row[2],
                        "genres": self._format_genres(row[3]),
                        "rating_count": row[4] or 0,
                        "decade": self._calculate_decade(row[2]),
                        "score": 0.0,
                        "strategy": "random",
                    }
                )

            return pd.DataFrame(results)
        finally:
            conn.close()

    def get_movie_info(self, movie_id: int) -> dict:
        """
        Get information about a specific movie from the database.

        Args:
            movie_id: MovieLens movieId

        Returns:
            Dictionary with movie information
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, title, year, genres
                FROM movies
                WHERE id = %s;
            """,
                (movie_id,),
            )

            row = cursor.fetchone()
            cursor.close()

            if row:
                return {
                    "movieId": row[0],
                    "title": row[1],
                    "year": row[2],
                    "genres": self._format_genres(row[3]),
                    "decade": self._calculate_decade(row[2]),
                }

            return {"error": f"Movie {movie_id} not found"}
        finally:
            conn.close()

    def search_movies(
        self, query: str, limit: int = 10, min_years_old: int = 0
    ) -> pd.DataFrame:
        """
        Search for movies by title in the database.

        Args:
            query: Search query (case-insensitive)
            limit: Maximum number of results
            min_years_old: Minimum age of movie in years

        Returns:
            DataFrame with matching movies
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Calculate max year
            import datetime

            current_year = datetime.date.today().year
            max_year = current_year - min_years_old

            cursor.execute(
                """
                SELECT id, title, year, genres
                FROM movies
                WHERE LOWER(title) LIKE %s
                AND year <= %s
                LIMIT %s;
            """,
                (f"%{query.lower()}%", max_year, limit),
            )

            rows = cursor.fetchall()
            cursor.close()

            results = []
            for row in rows:
                results.append(
                    {
                        "movieId": row[0],
                        "title": row[1],
                        "genres": self._format_genres(row[3]),
                        "decade": self._calculate_decade(row[2]),
                    }
                )

            return pd.DataFrame(results)
        finally:
            conn.close()


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Movie Recommendation System - Cold Start Demo")
    print("=" * 60)

    try:
        # Initialize recommender
        recommender = MovieRecommender()

        # Search for a movie
        print("\nSearching for 'Toy Story'...")
        search_results = recommender.search_movies("Toy Story", limit=5)
        print(search_results)

        # Example: User likes Toy Story (1), Jumanji (2), and The Lion King (364)
        liked_movies = [{"movieId": 1}, {"movieId": 2}, {"movieId": 364}]

        print("\nUser liked movies:")
        for mid in liked_movies:
            info = recommender.get_movie_info(mid["movieId"])
            print(f"  - {info.get('title', 'Unknown')}")

        print("\nGenerating recommendations...")
        recommendations = recommender.recommend(liked_movies, n_recommendations=10)

        print("\nTop 10 Recommendations:")
        print("-" * 60)
        for i, row in recommendations.iterrows():
            print(
                f"{int(i) + 1 if isinstance(i, (int, float, str)) else int(str(i)) + 1}. {row['title']}"
            )
            print(f"   Genres: {row['genres']} | Decade: {row['decade']}")
            print(f"   Score: {row['score']:.4f}")
            print()

        recommender.close()

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. PostgreSQL is running")
        print("2. The movies table is populated")
        print("3. DATABASE_URL is set correctly in .env")
        print("4. LightFM model files are in the models directory")
