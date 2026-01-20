# Song Content-Based Recommender: Evaluation Metrics and Performance Analysis

## 1. Introduction

## 2. Recommender Architecture

### 2.1 Algorithm Selection

The recommendation system utilizes **content-based filtering** with **approximate nearest neighbor (ANN) search** powered by PostgreSQL's pgvector extension. This approach generates recommendations based entirely on item features (song attributes), making it robust to cold-start problems for new users.

### 2.2 Recommender Configuration

| Parameter           | Value                                     |
| ------------------- | ----------------------------------------- |
| Embedding Dimension | 128                                       |
| Similarity Metric   | Cosine Distance                           |
| Index Type          | HNSW (Hierarchical Navigable Small World) |
| Database            | PostgreSQL with pgvector                  |

### 2.3 Feature Engineering

The embedding generation pipeline combines multiple feature types with weighted contributions:

| Feature Type   | Components                                         | Weight | Purpose                              |
| -------------- | -------------------------------------------------- | ------ | ------------------------------------ |
| Year           | Normalized release year                            | 1.5×   | Temporal clustering for era matching |
| Genre          | One-hot encoded (10 categories)                    | 1.2×   | Primary genre classification         |
| Audio Features | valence, energy, tempo, danceability, acousticness | 1.0×   | Sonic characteristic matching        |
| Niche Genres   | TF-IDF vectorization (100 features)                | 0.8×   | Sub-genre and scene context          |

The combined features produce a 116-dimensional vector, which is then zero-padded to the target 128 dimensions for consistent storage. All vectors are L2-normalized before insertion into the `song_vectors` table for efficient cosine similarity search.

## 3. Dataset

### 3.1 Dataset Overview

The embedding pipeline was constructed using the **550K Spotify Songs Audio, Lyrics & Genres** dataset.

| Statistic      | Value                        |
| -------------- | ---------------------------- |
| Total Songs    | 550,619                      |
| Unique Genres  | 10                           |
| Year Range     | 1900–2025                    |
| Audio Features | 11 Spotify audio descriptors |

### 3.2 Audio Features

The following Spotify audio features inform the recommendation similarity:

| Feature      | Description                     | Range    |
| ------------ | ------------------------------- | -------- |
| Danceability | Suitability for dancing         | 0.0–1.0  |
| Energy       | Perceptual measure of intensity | 0.0–1.0  |
| Valence      | Musical positiveness/happiness  | 0.0–1.0  |
| Tempo        | Beats per minute                | Variable |
| Acousticness | Acoustic vs. electronic quality | 0.0–1.0  |

## 4. Evaluation Methodology

### 4.1 Evaluation Approach

The system is evaluated using metrics that capture nostalgia-relevant qualities: temporal coherence, emotional consistency, and artist association. The evaluation sampled 100 random query songs and retrieved 10 nearest neighbors for each.

### 4.2 Metrics

#### Era Recall

Measures the proportion of recommendations from the same temporal era as the query, defined as within ±5 years:

$$
\text{Era Recall} = \frac{|\{r : |year_r - year_q| \leq 5\}|}{K}
$$

This metric captures temporal coherence, which is essential for nostalgia-focused recommendations where users expect content from a similar time period.

#### Popularity Drift

Measures the mean difference in popularity between query and recommended songs:

$$
\text{Popularity Drift} = \frac{1}{K} \sum_{i=1}^{K} (popularity_{r_i} - popularity_q)
$$

Negative values indicate recommendations of less mainstream songs (discovery), while positive values indicate more popular recommendations. Popularity is measured on Spotify's 0–100 scale.

#### Artist Continuity

Measures the proportion of recommendations sharing at least one artist with the query:

$$
\text{Artist Continuity} = \frac{|\{r : artists_r \cap artists_q \neq \emptyset\}|}{K}
$$

This captures scene-level associations, where familiar artists from the same era can enhance nostalgic response. Artist continuity emerges naturally from the embedding structure rather than being explicitly optimized.

#### Mood Consistency

Measures the proportion of recommendations within acceptable tolerance bands for emotional features. A recommendation is mood-consistent if at least 2 of 3 conditions hold:

- $|valence_r - valence_q| \leq 0.15$
- $|energy_r - energy_q| \leq 0.15$
- $|danceability_r - danceability_q| \leq 0.15$

This captures emotional similarity without requiring exact feature matching.

## 5. Results

### 5.1 Performance Summary

| Metric                | Value     | Interpretation                     |
| --------------------- | --------- | ---------------------------------- |
| Era Recall (±5 years) | **93.2%** | Strong temporal coherence          |
| Popularity Drift      | **+0.7**  | Near-neutral popularity matching   |
| Artist Continuity     | **17.5%** | Balanced familiarity and diversity |
| Mood Consistency      | **99.6%** | Excellent emotional coherence      |
| Duration Familiarity  | **15.3%** | Moderate song length matching      |

### 5.2 Analysis

#### Era Recall: 93.2%

The high era recall indicates that 93% of recommendations originate from the same ±5 year window as the query song. This temporal coherence is critical for nostalgia-focused applications, ensuring that recommended content evokes associations with the same cultural period as the seed song. The evaluation uses DISTINCT ON deduplication to ensure recommendations contain unique songs rather than multiple versions of the same track.

#### Popularity Drift: +0.7

The near-neutral popularity drift indicates that recommendations closely match the popularity level of query songs. This balanced approach ensures the system neither over-relies on mainstream hits nor pushes obscure tracks, providing recommendations that feel appropriately familiar to users.

#### Artist Continuity: 17.5%

The 17.5% artist continuity rate represents a balanced approach—sufficient to maintain scene-level coherence without becoming repetitive. This allows users to discover related artists from the same era while occasionally encountering familiar performers.

#### Mood Consistency: 99.6%

The near-perfect mood consistency demonstrates that recommendations preserve the emotional characteristics of query songs. The high score is expected given that audio features are weighted in the embedding and the tolerance-band definition (2-of-3 conditions within ±0.15) allows reasonable variation while ensuring perceptual similarity.

## 6. Technical Implementation

### 6.1 Similarity Search

Recommendations are generated using pgvector's cosine distance operator with duplicate filtering to ensure unique songs:

```sql
SELECT * FROM (
    SELECT DISTINCT ON (LOWER(SPLIT_PART(name, ' - ', 1)))
           id, name, artists, genre, year, distance
    FROM song_vectors sv
    JOIN songs s ON sv.spotify_id = s.id
    ORDER BY LOWER(SPLIT_PART(name, ' - ', 1)), distance
) sub
ORDER BY distance
LIMIT k;
```

The `DISTINCT ON` clause groups songs by their base title (before any " - " suffix like "Live" or "Remaster") and keeps only the closest match for each unique title. The HNSW index enables sub-second query times across the full 550K song corpus.

### 6.2 Pipeline Artifacts

| File                      | Description                                    |
| ------------------------- | ---------------------------------------------- |
| `audio_scaler.joblib`     | StandardScaler for audio feature normalization |
| `genre_encoder.joblib`    | OneHotEncoder for genre classification         |
| `tfidf_vectorizer.joblib` | TfidfVectorizer for niche genre text           |
| `training_config.joblib`  | Feature weights and pipeline configuration     |

## 7. Conclusion

The content-based song recommendation system demonstrates strong performance across all evaluation metrics. The 93.2% era recall and 99.6% mood consistency indicate that the system reliably produces recommendations that are both temporally coherent and emotionally consistent with query songs. The balanced artist continuity (17.5%) ensures diversity while maintaining scene-level associations. The implementation includes duplicate filtering using PostgreSQL's `DISTINCT ON` to prevent near-duplicate songs (remixes, live versions, remasters) from appearing in the same recommendation set. These characteristics make the system well-suited for nostalgia-focused recommendation applications where temporal and emotional context are primary user expectations.
