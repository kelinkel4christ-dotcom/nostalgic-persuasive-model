# Algorithms for Nostalgic Content Recommendation

This document provides a formal description of the algorithms used in the Nostalgic Persuasive Recommendation System. The algorithms are presented in pseudocode format suitable for academic documentation.

---

## 1. Recommendation Flow Algorithm

The main recommendation algorithm orchestrates multiple subsystems to deliver personalized nostalgic content to users. The pipeline processes user context, generates candidates from multiple sources, applies nostalgia filtering, and uses a contextual bandit for final selection.

### Algorithm 1: Get Personalized Recommendation

```
Algorithm: GET_RECOMMENDATION(user_id, journal_text)

Input:
  - user_id: Unique identifier for the user
  - journal_text: Optional text from user's journal entry

Output:
  - recommendation: Selected nostalgic content (movie or song)
  - stress_score: Detected stress level (0-1)
  - emotion: Detected emotional state
  - bandit_score: Confidence score from contextual bandit

Procedure:
  1. FETCH USER DATA
     prefs ← FetchUserPreferences(user_id)
     birth_year ← prefs.birth_year
     liked_movies ← prefs.selected_movie_ids ∪ prefs.feedback_history[type="movie"]
     liked_songs ← prefs.selected_song_ids ∪ prefs.feedback_history[type="song"]
     recent_feedback ← FetchRecentFeedback(user_id, limit=50)

  2. ANALYZE USER CONTEXT
     IF journal_text is not empty THEN
       stress_score ← StressDetector.predict(journal_text)
       emotion_result ← EmotionDetector.predict(journal_text)
     ELSE
       cached_context ← FetchLatestContext(user_id)
       stress_score ← cached_context.stress_score
       emotion_result ← {emotion: cached_context.emotion, confidence: 1.0}
     END IF

  3. BUILD CONTEXT VECTOR
     user_positive_rate ← CalculatePositiveRate(recent_feedback)
     context ← BuildContextFeatures(stress_score, emotion_result.emotion,
                                     user_positive_rate, birth_year)

  4. GENERATE CANDIDATES
     candidates ← ∅

     // Generate movie candidates
     movie_df ← MovieRecommender.recommend(liked_movies, n=50)
     FOR EACH movie IN movie_df DO
       ns ← NostalgiaScore(birth_year, movie.year, movie.rating_count)
       candidates ← candidates ∪ {
         type: "movie", id: movie.id, title: movie.title,
         genres: movie.genres, year: movie.year,
         nostalgia_score: ns, similarity_score: movie.score
       }
     END FOR

     // Generate song candidates
     song_df ← SongRecommender.recommend(liked_songs, n=50)
     FOR EACH song IN song_df DO
       ns ← NostalgiaScore(birth_year, song.year, song.popularity, linear=true)
       candidates ← candidates ∪ {
         type: "song", id: song.id, name: song.name,
         artists: song.artists, genre: song.genre, year: song.year,
         nostalgia_score: ns, similarity_score: song.score
       }
     END FOR

  5. FILTER CANDIDATES
     // Remove recently shown items
     recent_ids ← {f.content_id : f ∈ recent_feedback}
     candidates ← {c ∈ candidates : c.id ∉ recent_ids}

     // Apply nostalgia threshold filter
     MIN_NOSTALGIA_SCORE ← 0.3
     nostalgic_candidates ← {c ∈ candidates : c.nostalgia_score ≥ MIN_NOSTALGIA_SCORE}

     IF |nostalgic_candidates| > 0 THEN
       candidates ← nostalgic_candidates
     END IF

  6. BANDIT SELECTION
     // Shuffle to prevent positional bias
     Shuffle(candidates)

     // Select using hierarchical bandit
     (selected_idx, bandit_score) ← Bandit.select(user_id, context, candidates)

     // Within-arm stochastic selection for variety
     selected_arm ← GetArm(candidates[selected_idx])
     arm_candidates ← {c ∈ candidates : GetArm(c) = selected_arm}
     Sort(arm_candidates, by: similarity_score, descending)
     top_5 ← arm_candidates[0:5]
     selected ← RandomChoice(top_5)

  7. RETURN RESULT
     RETURN (selected, stress_score, emotion_result, bandit_score)
```

### Algorithm 2: Process User Feedback

```
Algorithm: PROCESS_FEEDBACK(user_id, content_id, content_type,
                            content_year, content_genre, brings_back_memories)

Input:
  - user_id: Unique identifier for the user
  - content_id: Identifier of the recommended content
  - content_type: "movie" or "song"
  - content_year: Release year of content
  - content_genre: Genre of content
  - brings_back_memories: Boolean user response to "Does this bring back memories?"

Output:
  - success: Boolean indicating successful update

Procedure:
  1. FETCH USER CONTEXT
     prefs ← FetchUserPreferences(user_id)
     birth_year ← prefs.birth_year
     recent_feedback ← FetchRecentFeedback(user_id)
     user_positive_rate ← CalculatePositiveRate(recent_feedback)

  2. BUILD CONTEXT VECTOR
     context ← BuildContextFeatures(
       stress_score=0.5,  // Neutral for update
       emotion="neutral",
       user_positive_rate,
       birth_year
     )

  3. CALCULATE REWARD
     IF brings_back_memories THEN
       reward ← 1.0
     ELSE
       reward ← 0.0
     END IF

  4. CONSTRUCT CANDIDATE REPRESENTATION
     candidate ← {
       type: content_type,
       id: content_id,
       year: content_year,
       genre: content_genre,
       genres: content_genre
     }

  5. UPDATE BANDIT
     Bandit.update(user_id, context, candidate, reward)

  6. RETURN success ← true
```

---

## 2. Nostalgia Score Assignment Algorithm

The nostalgia score quantifies how likely a piece of content is to evoke nostalgic feelings for a specific user. The algorithm combines psychological models of personal nostalgia (the reminiscence bump) with cultural nostalgia (popular content experienced indirectly).

### Algorithm 3: Calculate Nostalgia Score

```
Algorithm: NOSTALGIA_SCORE(birth_year, release_year, rating_count,
                           max_count, use_linear=false)

Input:
  - birth_year: User's year of birth
  - release_year: Year the content was released
  - rating_count: Popularity metric (rating count or Spotify popularity)
  - max_count: Maximum value for normalization
  - use_linear: If true, use linear scaling; otherwise use logarithmic scaling

Output:
  - score: Nostalgia score in range [0, 1]

Constants:
  - PEAK_AGE ← 13        // Age when nostalgia peaks (reminiscence bump)
  - WIDTH ← 8            // Gaussian curve width
  - PREBIRTH_DECAY ← 0.03 // Decay rate for pre-birth content
  - CULTURAL_WEIGHT ← 0.4 // Maximum cultural nostalgia contribution
  - BASE_WEIGHT ← 0.7    // Base personal nostalgia weight
  - POP_BOOST ← 0.3      // Maximum popularity boost

Procedure:
  1. CALCULATE AGE AT RELEASE
     age_at_release ← release_year - birth_year

  2. CALCULATE AGE-BASED NOSTALGIA (Reminiscence Bump Model)
     IF age_at_release ≥ 0 THEN
       // Post-birth: Gaussian centered at PEAK_AGE
       age_score ← exp(-((age_at_release - PEAK_AGE)² / (2 × WIDTH²)))
     ELSE
       // Pre-birth: Exponential decay from birth point
       birth_score ← exp(-((0 - PEAK_AGE)² / (2 × WIDTH²)))
       age_score ← birth_score × exp(-PREBIRTH_DECAY × |age_at_release|)
     END IF

  3. CALCULATE POPULARITY SCORE
     IF rating_count ≤ 0 OR max_count ≤ 0 THEN
       pop_score ← 0.0
     ELSE IF use_linear THEN
       // Linear scaling for pre-normalized metrics (e.g., Spotify popularity 0-100)
       pop_score ← min(1.0, rating_count / max_count)
     ELSE
       // Logarithmic scaling for raw counts (prevents mega-hits from dominating)
       pop_score ← log(1 + rating_count) / log(1 + max_count)
     END IF

  4. CALCULATE PERSONAL NOSTALGIA COMPONENT
     // Popularity boosts but cannot create personal nostalgia
     personal ← age_score × (BASE_WEIGHT + POP_BOOST × pop_score)

  5. CALCULATE CULTURAL NOSTALGIA COMPONENT
     // Only applies to pre-birth content (inherited cultural memory)
     IF age_at_release < 0 THEN
       cultural ← pop_score × CULTURAL_WEIGHT
     ELSE
       cultural ← 0.0
     END IF

  6. COMBINE AND CLAMP
     final_score ← personal + cultural
     score ← min(1.0, max(0.0, final_score))

  7. RETURN round(score, 3)
```

### Algorithm 3a: Age-Based Nostalgia (Sub-function)

```
Algorithm: AGE_NOSTALGIA(age_at_release)

Input:
  - age_at_release: User's age when content was released (can be negative)

Output:
  - score: Age-based nostalgia score in range [0, 1]

Constants:
  - PEAK_AGE ← 13        // Based on psychology research on reminiscence bump
  - WIDTH ← 8            // Standard deviation of Gaussian
  - PREBIRTH_DECAY ← 0.03 // Decay rate for content released before birth

Procedure:
  IF age_at_release ≥ 0 THEN
    // Post-birth content: Use Gaussian distribution centered at peak age
    // Maximum nostalgia at PEAK_AGE, decreasing for content consumed earlier or later
    score ← exp(-((age_at_release - PEAK_AGE)² / (2 × WIDTH²)))
  ELSE
    // Pre-birth content: Start from birth score and apply exponential decay
    // Older pre-birth content has progressively lower nostalgia potential
    birth_point_score ← exp(-((0 - PEAK_AGE)² / (2 × WIDTH²)))
    score ← birth_point_score × exp(-PREBIRTH_DECAY × |age_at_release|)
  END IF

  RETURN score
```

### Algorithm 3b: Popularity Score (Sub-function)

```
Algorithm: POPULARITY_SCORE(rating_count, max_count, use_linear=false)

Input:
  - rating_count: Number of ratings or popularity metric for this content
  - max_count: Maximum rating count in the dataset
  - use_linear: If true, use linear scaling

Output:
  - score: Popularity score in range [0, 1]

Procedure:
  IF rating_count ≤ 0 OR max_count ≤ 0 THEN
    RETURN 0.0
  END IF

  IF use_linear THEN
    // Linear scaling: Direct proportion (for pre-normalized values like Spotify 0-100)
    RETURN min(1.0, rating_count / max_count)
  ELSE
    // Log scaling: Compresses large values, prevents mega-hits from dominating
    // A movie with 10,000 ratings scores ~0.8 vs 1.0 for 100,000 ratings
    RETURN log(1 + rating_count) / log(1 + max_count)
  END IF
```

---

## 3. Contextual Bandit Selection Algorithm

The system uses a Hierarchical LinUCB (Linear Upper Confidence Bound) contextual bandit to select optimal content based on the user's current context. The algorithm balances exploitation (recommending content known to evoke nostalgia) with exploration (trying new content to learn user preferences).

### Algorithm 4: Hierarchical Bandit Selection

```
Algorithm: HIERARCHICAL_SELECT(user_id, context, candidates)

Input:
  - user_id: Unique identifier for the user
  - context: Context feature vector (stress, emotion, history, birth_year)
  - candidates: List of candidate content items

Output:
  - selected_idx: Index of selected candidate
  - bandit_score: Confidence score for selection

Constants:
  - MIN_USER_UPDATES ← 10  // Minimum interactions before using personalized model
  - MAX_BLEND ← 0.7        // Maximum weight for user model

Procedure:
  1. GLOBAL MODEL SELECTION
     (global_idx, global_score) ← GlobalModel.select(context, candidates)

  2. CHECK FOR PERSONALIZATION ELIGIBILITY
     user_model ← GetOrCreateUserModel(user_id)

     IF user_model.n_updates < MIN_USER_UPDATES THEN
       // Cold-start user: Use global model only
       RETURN (global_idx, global_score)
     END IF

  3. USER MODEL SELECTION
     (user_idx, user_score) ← user_model.select(context, candidates)

  4. BLEND PREDICTIONS
     // Blend weight increases with user interactions (up to MAX_BLEND)
     blend ← min(user_model.n_updates / 50, MAX_BLEND)

     // Compare weighted scores
     IF user_score × blend > global_score × (1 - blend) THEN
       RETURN (user_idx, user_score)
     ELSE
       RETURN (global_idx, global_score)
     END IF
```

### Algorithm 5: LinUCB Arm Selection

```
Algorithm: LINUCB_SELECT(context, candidates)

Input:
  - context: Context feature vector (d dimensions)
  - candidates: List of candidate content items

Output:
  - selected_idx: Index of candidate with highest UCB score
  - ucb_score: Upper confidence bound score

Constants:
  - α (alpha): Exploration parameter (higher = more exploration)
  - ARMS: Set of genre-based arms {"drama", "comedy", "action", "romance",
          "thriller", "other_movie", "pop", "rock", "hiphop", "rnb",
          "country", "other_song"}

Procedure:
  1. ENSURE CONTEXT SHAPE
     x ← EnsureShape(context, dimensions=d)

  2. IF model is not fitted THEN
     // Random selection for uninitialized model
     idx ← RandomInteger(0, |candidates| - 1)
     RETURN (idx, 0.5)
  END IF

  3. MAP CANDIDATES TO ARMS
     FOR EACH candidate IN candidates DO
       arm ← GetArmFromCandidate(candidate)  // Genre normalization
       candidate.arm ← arm
     END FOR

  4. COMPUTE UCB SCORES FOR EACH CANDIDATE
     scores ← []
     FOR i ← 0 TO |candidates| - 1 DO
       arm ← candidates[i].arm

       IF arm ∈ ARMS THEN
         // LinUCB formula: θ̂ᵀx + α√(xᵀA⁻¹x)
         // MABWiser computes this internally via predict_expectations
         expectations ← MAB.predict_expectations(x)
         score ← expectations[arm]
       ELSE
         score ← 0.5  // Default for unknown arms
       END IF

       scores.append((i, score))
     END FOR

  5. SELECT BEST ARM
     Sort(scores, by: score, descending)
     (best_idx, best_score) ← scores[0]

  6. RETURN (best_idx, best_score)
```

### Algorithm 6: LinUCB Model Update

```
Algorithm: LINUCB_UPDATE(context, candidate, reward)

Input:
  - context: Context feature vector
  - candidate: The content item that was recommended
  - reward: Observed reward (1.0 for positive feedback, 0.0 for negative)

Procedure:
  1. PREPARE INPUTS
     x ← EnsureShape(context, dimensions=d)
     arm ← GetArmFromCandidate(candidate)
     binary_reward ← 1 IF reward > 0.5 ELSE 0

  2. UPDATE MODEL
     IF model is not fitted THEN
       // First observation: Initialize with fit
       MAB.fit(decisions=[arm], rewards=[binary_reward], contexts=x)
       is_fitted ← true
     ELSE
       // Incremental update with new observation
       MAB.partial_fit(decisions=[arm], rewards=[binary_reward], contexts=x)
     END IF

  3. INCREMENT UPDATE COUNTER
     n_updates ← n_updates + 1
```

---

## 4. Context Feature Construction

The context vector encodes the user's current state for the contextual bandit.

### Algorithm 7: Build Context Features

```
Algorithm: BUILD_CONTEXT_FEATURES(stress_score, emotion,
                                   user_positive_rate, birth_year)

Input:
  - stress_score: Detected stress level (0.0 to 1.0)
  - emotion: Detected emotion string
  - user_positive_rate: Historical positive feedback rate (0.0 to 1.0)
  - birth_year: User's year of birth

Output:
  - context: Feature vector of dimension 12

Constants:
  - EMOTIONS ← ["anger", "fear", "joy", "love", "neutral", "sadness", "surprise"]
  - BIRTH_YEAR_CENTER ← 2000
  - BIRTH_YEAR_SCALE ← 40
  - CONTEXT_DIM ← 12

Procedure:
  features ← []

  1. STRESS FEATURE (1 dimension)
     features.append(stress_score)

  2. EMOTION ONE-HOT ENCODING (7 dimensions)
     FOR EACH e IN EMOTIONS DO
       IF e = emotion THEN
         features.append(1.0)
       ELSE
         features.append(0.0)
       END IF
     END FOR

  3. USER HISTORY FEATURE (1 dimension)
     features.append(user_positive_rate)

  4. BIRTH YEAR FEATURE (1 dimension)
     IF birth_year is not null THEN
       normalized_birth_year ← (birth_year - BIRTH_YEAR_CENTER) / BIRTH_YEAR_SCALE
     ELSE
       normalized_birth_year ← 0.0
     END IF
     features.append(normalized_birth_year)

  5. PADDING (2 dimensions)
     WHILE |features| < CONTEXT_DIM DO
       features.append(0.0)
     END WHILE

  6. RETURN features[0:CONTEXT_DIM]
```

---

## 5. Genre Normalization

Genres are normalized to a fixed set of arms for the contextual bandit.

### Algorithm 8: Genre Normalization

```
Algorithm: NORMALIZE_GENRE(raw_genre, content_type)

Input:
  - raw_genre: Raw genre string (may contain multiple genres separated by "|")
  - content_type: "movie" or "song"

Output:
  - normalized: One of the 12 canonical genre arms

Constants:
  MOVIE_GENRE_MAP ← {
    "drama" → "drama", "comedy" → "comedy", "action" → "action",
    "adventure" → "action", "romance" → "romance", "thriller" → "thriller",
    "horror" → "thriller", "crime" → "thriller", "sci-fi" → "action",
    "animation" → "comedy", "family" → "comedy", "fantasy" → "action",
    "mystery" → "thriller", "war" → "drama", "documentary" → "other_movie",
    "musical" → "comedy", "history" → "drama"
  }

  SONG_GENRE_MAP ← {
    "pop" → "pop", "rock" → "rock", "alternative" → "rock", "indie" → "rock",
    "hip hop" → "hiphop", "hip-hop" → "hiphop", "rap" → "hiphop",
    "r&b" → "rnb", "rnb" → "rnb", "soul" → "rnb", "blues" → "rnb",
    "country" → "country", "folk" → "country",
    "electronic" → "pop", "dance" → "pop", "edm" → "pop", "latin" → "pop",
    "metal" → "rock", "punk" → "rock",
    "jazz" → "other_song", "classical" → "other_song", "reggae" → "other_song"
  }

Procedure:
  IF raw_genre is empty THEN
    IF content_type = "movie" THEN
      RETURN "other_movie"
    ELSE
      RETURN "other_song"
    END IF
  END IF

  // Extract first genre if multiple
  first_genre ← raw_genre.split("|")[0].toLowerCase().trim()

  IF content_type = "movie" THEN
    IF first_genre ∈ MOVIE_GENRE_MAP THEN
      RETURN MOVIE_GENRE_MAP[first_genre]
    ELSE
      RETURN "other_movie"
    END IF
  ELSE
    IF first_genre ∈ SONG_GENRE_MAP THEN
      RETURN SONG_GENRE_MAP[first_genre]
    ELSE
      RETURN "other_song"
    END IF
  END IF
```

---

## Summary of Algorithm Parameters

| Algorithm           | Parameter             | Default Value | Description                                  |
| ------------------- | --------------------- | ------------- | -------------------------------------------- |
| Nostalgia Score     | `PEAK_AGE`            | 13            | Age when nostalgia peaks (reminiscence bump) |
| Nostalgia Score     | `WIDTH`               | 8             | Gaussian curve width                         |
| Nostalgia Score     | `PREBIRTH_DECAY`      | 0.03          | Decay rate for pre-birth content             |
| Nostalgia Score     | `CULTURAL_WEIGHT`     | 0.4           | Maximum cultural nostalgia contribution      |
| Nostalgia Score     | `MIN_NOSTALGIA_SCORE` | 0.3           | Threshold for nostalgic content              |
| LinUCB              | `α (alpha)`           | 1.0           | Exploration parameter                        |
| LinUCB              | `CONTEXT_DIM`         | 12            | Number of context features                   |
| Hierarchical Bandit | `MIN_USER_UPDATES`    | 10            | Interactions before personalization          |
| Hierarchical Bandit | `MAX_BLEND`           | 0.7           | Maximum personalization weight               |
| Recommender         | `MAX_MOVIE_RATINGS`   | 100,000       | Normalization constant for movie popularity  |
| Recommender         | `MAX_SONG_POPULARITY` | 100           | Normalization constant for song popularity   |

---

## Complexity Analysis

| Algorithm          | Time Complexity | Space Complexity |
| ------------------ | --------------- | ---------------- |
| Get Recommendation | O(n + m)        | O(n + m)         |
| Nostalgia Score    | O(1)            | O(1)             |
| LinUCB Select      | O(k × d²)       | O(k × d²)        |
| LinUCB Update      | O(d²)           | O(d²)            |
| Context Features   | O(1)            | O(d)             |

Where:

- n = number of movie candidates
- m = number of song candidates
- k = number of arms (genres)
- d = context dimension

---

## References

1. **Reminiscence Bump**: Rubin, D. C., & Schulkind, M. D. (1997). The distribution of autobiographical memories across the lifespan. _Memory & Cognition_, 25(6), 859-866.

2. **LinUCB Algorithm**: Li, L., Chu, W., Langford, J., & Schapire, R. E. (2010). A contextual-bandit approach to personalized news article recommendation. _Proceedings of the 19th International Conference on World Wide Web_, 661-670.

3. **Multi-Armed Bandits**: Slivkins, A. (2019). Introduction to multi-armed bandits. _Foundations and Trends in Machine Learning_, 12(1-2), 1-286.
