import os
import joblib
import numpy as np
import pandas as pd
from lightfm import LightFM

# Paths (from training/test/ directory)
MODEL_DIR = "../../models/movie_recommender"
DATASET_DIR = "../../dataset/ml-32m"
MOVIES_FILE = os.path.join(DATASET_DIR, "movies.csv")

def load_artifacts():
    print("Loading model items...")
    model = joblib.load(os.path.join(MODEL_DIR, "lightfm_model.pkl"))
    dataset = joblib.load(os.path.join(MODEL_DIR, "lightfm_dataset.pkl"))
    item_features = joblib.load(os.path.join(MODEL_DIR, "item_features.pkl"))
    return model, dataset, item_features

def get_recommendations(model, dataset, item_features, user_ids, movies_df, top_k=5):
    n_users, n_items = dataset.interactions_shape()
    
    # Internal mappings
    user_id_map, user_feature_map, item_id_map, item_feature_map = dataset.mapping()
    
    # Reverse item mapping: internal_id -> movie_id
    reverse_item_map = {v: k for k, v in item_id_map.items()}
    
    for user_id in user_ids:
        # In a real app, you'd check if user exists in training data
        # If new user, you'd need to add them to dataset or use cold-start strategy
        # Here we assume user exists or we treat them as a new user (internal id 0?)
        # Actually LightFM can predict for new users if we provide user features, 
        # but without user features it's just based on item popularity/biases.
        
        # For simplicity, let's use a known internal user ID or 0
        try:
            internal_user_id = user_id_map[user_id]
        except KeyError:
            print(f"User {user_id} not found in training data. Using ID 0 (cold start approximation).")
            internal_user_id = 0

        scores = model.predict(
            internal_user_id,
            np.arange(n_items),
            item_features=item_features,
            num_threads=1
        )
        
        top_items = np.argsort(-scores)[:top_k]
        
        print(f"\nRecommendations for User {user_id}:")
        for internal_item_id in top_items:
            movie_id = reverse_item_map[internal_item_id]
            movie_title = movies_df[movies_df['movieId'] == movie_id]['title'].values[0]
            print(f"- {movie_title} (Score: {scores[internal_item_id]:.2f})")

def main():
    if not os.path.exists(MODEL_DIR):
        print(f"Model directory {MODEL_DIR} does not exist. Train the model first.")
        return

    model, dataset, item_features = load_artifacts()
    
    # Verify dataset size
    n_users, n_items = dataset.interactions_shape()
    print(f"Loaded Model Stats: {n_users} Users, {n_items} Items")
    
    # Load movies for titles
    movies = pd.read_csv(MOVIES_FILE)
    
    # Test users (Ids from the rating sample, e.g., 1, 2, 3)
    test_users = [1, 2, 3] 
    
    get_recommendations(model, dataset, item_features, test_users, movies)

if __name__ == "__main__":
    main()
