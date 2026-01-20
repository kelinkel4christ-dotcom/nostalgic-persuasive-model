# Algorithm Documentation

## Overview

The system employs four main algorithmic approaches to deliver personalized nostalgic content recommendations:

1.  **Collaborative Filtering** - For movie recommendations
2.  **Content-Based Filtering** - For song recommendations
3.  **Contextual Bandit** - For optimal content selection
4.  **Text Classification** - For stress and emotion detection

---

## 1. Collaborative Filtering (Movies)

### Algorithm: Matrix Factorization with User Folding

**Purpose**: Generate movie recommendations for new users based on movies they've liked.

### Step-by-Step Process

1.  **Get Liked Movies**: Retrieve the list of movies the user has explicitly liked during onboarding, along with the timestamp of each like.

2.  **Calculate Recency Weights**: Apply an exponential decay function to give more weight to recently liked items.
    - Formula: `weight(t) = exp(-λ × days_since(t))`
    - Result: Recent selections have a higher influence on the resulting user embedding.

3.  **Build Pseudo-User Embedding**: Construct a vector representation for the new user without retraining the model ("User Folding").
    - Retrieve the pre-trained item embeddings for each liked movie.
    - Multiply each item embedding by its calculated recency weight.
    - Sum all weighted embeddings and normalize to a unit vector.

4.  **Score All Movies**: Calculate the affinity between the user and every movie in the catalog.
    - Compute the dot product between the User Embedding and the Movie Item Embedding.
    - **Filter 1**: Keep only movies released during the user's "Nostalgia Period" (ages 5-18).
    - **Filter 2**: Exclude movies the user has already liked.

5.  **Return Top-N**: Sort the remaining movies by score (descending) and return the top N candidates.

### Key Concepts

- **User Folding**: Allows handling cold-start users by approximating their latent features from items they like.
- **Nostalgic Period**: A calculated date range specific to each user's birth year.

---

## 2. Content-Based Filtering (Songs)

### Algorithm: Vector Similarity with Learned Embeddings

**Purpose**: Find songs similar to what the user has liked based on audio features and lyrics.

### Step-by-Step Process

1.  **Get Liked Songs**: Retrieve the user's liked songs, which contain raw Metadata and Spotify Audio Features (e.g., danceability, energy, valence).

2.  **Create Feature Vectors**: Transform raw song data into a dense numerical vector.
    - **Scale**: Normalize numerical features using a simplistic StandardScaler.
    - **Encode**: One-hot encode genre tags using MultiLabelBinarizer.
    - **Vectorize**: Convert lyrics to TF-IDF vectors to capture thematic similarity.
    - **Concatenate**: Combine all features and reduce dimensionality (e.g., via PCA) to 128 dimensions.

3.  **Calculate Centroid**: detailed user profile creation.
    - Apply recency weights to each liked song's vector.
    - Compute the weighted mean (centroid) of all liked song vectors. This single vector represents the user's current music taste.

4.  **Query Vector Database**: Perform a similarity search in the `pgvector` database.
    - Metric: Cosine Similarity (1 - Cosine Distance).
    - Find the nearest neighbors to the user's centroid vector.

5.  **Filter & Return**:
    - Apply the **Nostalgic Period** filter.
    - Remove duplicates/liked songs.
    - Return the top N matches.

### Key Concepts

- **Embeddings**: Dense vector representations that capture the semantic "feeling" of a song.
- **Centroid**: The mathematical "center" of a user's taste cluster.

---

## 3. Contextual Bandit (Content Selection)

### Algorithm: Hierarchical LinUCB (Linear Upper Confidence Bound)

**Purpose**: Select the best content type (Song or Movie) and specific item based on the user's immediate context.

### The Problem

Traditional recommendation systems are static. A contextual bandit learns online: it observes the user's state (Context), takes an action (Recommendation), and receives feedback (Reward), constantly updating its policy to maximize future rewards.

### Step-by-Step Process

1.  **Build Context Vector**: gather current signals about the user.
    - **Stress Level**: 0.0 to 1.0 (from text analysis).
    - **Emotion**: One-hot encoded vector of 7 emotions.
    - **Time**: Hour of day, day of week.
    - **History**: Positive feedback rate.

2.  **Generate Candidates**:
    - Fetch top movies from Movie Recommender.
    - Fetch top songs from Song Recommender.
    - These form the "Arms" of the bandit for this round.

3.  **Calculate UCB Scores**: For each candidate (Arm), calculate a score using the LinUCB formula:
    - `Score = Prediction + Exploration_Bonus`
    - `Prediction`: How likely the user is to like this specific item given the current context (Exploitation).
    - `Exploration_Bonus`: A value representing uncertainty. Represents how "unknown" this item/context pair is. High uncertainty = higher chance to be picked to learn more (Exploration).

4.  **Select Best Arm**: Pick the candidate with the highest UCB score.
    - This automatically balances showing safe bets (high prediction) vs. trying new things (high exploration).

5.  **Hierarchical Decision**:
    - **Cold Start**: If the user has < 10 interactions, use the **Global Model** (trained on everyone).
    - **Personalized**: If the user has ≥ 10 interactions, blend the Global Model with a **User-Specific Model**.

6.  **Update Model**: When the user provides feedback (e.g., "This brings back memories"):
    - Reward = 1 (Positive) or 0 (Negative).
    - Update the model weights (`A` matrix and `b` vector) instantly. The system learns effectively in real-time.

---

## 4. Text Classification (Stress/Emotion)

### Algorithm: Transformer-Based Sequence Classification (RoBERTa)

**Purpose**: Analyze journal entries to detect the user's mental state.

### Step-by-Step Process

1.  **Input Processing**:
    - Take the raw text string (e.g., "I'm feeling really overwhelmed today.").
    - **Tokenize**: Break into sub-word tokens using the specific tokenizer for the model (RoBERTa or DistilRoBERTa).
    - Add special tokens (`[CLS]`, `[SEP]`).

2.  **Forward Pass**:
    - Pass tokens through the Transformer layers (Self-Attention mechanism).
    - Extract the final embedding of the `[CLS]` token, which represents the aggregate meaning of the entire sentence.

3.  **Classification Head**:
    - **Stress**: Pass `[CLS]` embedding through a linear layer -> Softmax -> Output Probability (Stress Score 0.0 - 1.0).
    - **Emotion**: Pass `[CLS]` embedding through a linear layer -> Sigmoid -> Output Probabilities for 7 classes (Anger, Fear, Joy, Love, Neutral, Sadness, Surprise).

4.  **Thresholding (Emotion only)**:
    - The model outputs independent probabilities for each emotion.
    - Apply a tuned threshold (e.g., 0.5). If multiple emotions are above the threshold, return all of them. If none, return the one with the highest raw score.

### Key Concepts

- **Transfer Learning**: We use models pre-trained on massive text corpora and fine-tuned on specific psychological datasets.
- **Attention**: The model "pays attention" to specific words like "overwhelmed" or "happy" to determine the final classification.
