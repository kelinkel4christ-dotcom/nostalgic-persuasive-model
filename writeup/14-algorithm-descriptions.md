# Algorithm Descriptions for Nostalgic Content Recommendation

This document provides formal step-by-step descriptions of the algorithms used in the Nostalgic Persuasive Recommendation System. Each algorithm is described in plain English suitable for academic documentation.

---

## 1. Recommendation Flow Algorithm

The main recommendation algorithm orchestrates multiple subsystems to deliver personalized nostalgic content to users. The pipeline processes user context, generates candidates from multiple sources, applies nostalgia filtering, and uses a contextual bandit for final selection.

### Algorithm 1: Get Personalized Recommendation

**Input:**

- `user_id`: Unique identifier for the user
- `journal_text`: Optional text from user's journal entry

**Output:**

- `recommendation`: Selected nostalgic content (movie or song)
- `stress_score`: Detected stress level (0-1)
- `emotion`: Detected emotional state
- `bandit_score`: Confidence score from contextual bandit

**Procedure:**

**Step 1: Fetch User Data**

1. Retrieve the user's preferences from the database using the user identifier.
2. Extract the user's birth year from the preferences.
3. Compile the list of liked movies by combining the movie identifiers selected during onboarding with any movies from the user's positive feedback history.
4. Compile the list of liked songs by combining the song identifiers selected during onboarding with any songs from the user's positive feedback history.
5. Retrieve the user's recent feedback records, limited to the most recent 50 interactions.

**Step 2: Analyze User Context**

1. If the journal text is provided and not empty:
   - Pass the journal text to the Stress Detector model and store the returned stress score.
   - Pass the journal text to the Emotion Detector model and store the returned emotion result containing the emotion label, confidence, and probability distribution.
2. Otherwise, if no journal text is provided:
   - Retrieve the cached context from the database for this user.
   - Use the cached stress score and emotion values.

**Step 3: Build Context Vector**

1. Calculate the user's positive feedback rate by dividing the count of positive feedback events by the total number of recent feedback events.
2. Construct the context feature vector by invoking the Build Context Features procedure with the stress score, detected emotion, positive feedback rate, and birth year.

**Step 4: Generate Candidates**

1. Initialize an empty list to hold candidate content items.
2. Generate movie candidates:
   - Invoke the Movie Recommender with the list of liked movies, requesting 50 recommendations.
   - For each movie returned by the recommender:
     - Calculate the nostalgia score using the user's birth year, the movie's release year, and the movie's rating count.
     - Create a candidate record containing the content type as "movie", the movie identifier, title, genres, release year, rating count, nostalgia score, and similarity score.
     - Add the candidate record to the candidates list.
3. Generate song candidates:
   - Invoke the Song Recommender with the list of liked songs, requesting 50 recommendations.
   - For each song returned by the recommender:
     - Calculate the nostalgia score using the user's birth year, the song's release year, and the song's popularity value with linear scaling enabled.
     - Create a candidate record containing the content type as "song", the song identifier, name, artists, genre, release year, popularity, nostalgia score, and similarity score.
     - Add the candidate record to the candidates list.

**Step 5: Filter Candidates**

1. Collect the content identifiers from all recent feedback records into a set.
2. Remove from the candidates list any candidate whose identifier appears in the recent feedback set.
3. Define the minimum nostalgia score threshold as 0.3.
4. Create a filtered list containing only candidates with nostalgia scores greater than or equal to the threshold.
5. If the filtered list is not empty, replace the candidates list with the filtered list.
6. If the filtered list is empty, retain all candidates since they already satisfy the 10-year minimum age requirement from the recommenders.

**Step 6: Bandit Selection**

1. Randomly shuffle the candidates list to prevent positional bias.
2. Invoke the Bandit selection procedure with the user identifier, context vector, and candidates list to obtain the selected index and bandit score.
3. Determine the genre arm of the selected candidate.
4. Collect all candidates belonging to the same genre arm as the selected candidate.
5. Sort these same-arm candidates by similarity score in descending order.
6. Take the top 5 candidates from this sorted list.
7. Randomly select one candidate from these top 5 as the final selection.

**Step 7: Return Result**

1. Return the selected content, stress score, emotion result, and bandit score.

---

### Algorithm 2: Process User Feedback

**Input:**

- `user_id`: Unique identifier for the user
- `content_id`: Identifier of the recommended content
- `content_type`: Either "movie" or "song"
- `content_year`: Release year of content
- `content_genre`: Genre of content
- `brings_back_memories`: Boolean user response to "Does this bring back memories?"

**Output:**

- `success`: Boolean indicating successful update

**Procedure:**

**Step 1: Fetch User Context**

1. Retrieve the user's preferences from the database.
2. Extract the birth year from the preferences, defaulting to 2000 if not available.
3. Retrieve the user's recent feedback records.
4. Calculate the user's positive feedback rate from the recent feedback.

**Step 2: Build Context Vector**

1. Construct the context feature vector using a neutral stress score of 0.5, a neutral emotion label, the user's positive feedback rate, and the user's birth year.

**Step 3: Calculate Reward**

1. If the user indicated the content brought back memories, set the reward to 1.0.
2. Otherwise, set the reward to 0.0.

**Step 4: Construct Candidate Representation**

1. Create a candidate record containing the content type, content identifier, release year, and genre information.

**Step 5: Update Bandit**

1. Invoke the Bandit update procedure with the user identifier, context vector, candidate record, and reward value.

**Step 6: Return Success**

1. Return true to indicate the feedback was processed successfully.

---

## 2. Nostalgia Score Assignment Algorithm

The nostalgia score quantifies how likely a piece of content is to evoke nostalgic feelings for a specific user. The algorithm combines psychological models of personal nostalgia (the reminiscence bump) with cultural nostalgia (popular content experienced indirectly).

### Algorithm 3: Calculate Nostalgia Score

**Input:**

- `birth_year`: User's year of birth
- `release_year`: Year the content was released
- `rating_count`: Popularity metric (rating count or Spotify popularity)
- `max_count`: Maximum value for normalization
- `use_linear`: If true, use linear scaling; otherwise use logarithmic scaling

**Output:**

- `score`: Nostalgia score in range [0, 1]

**Constants:**

- Peak Age = 13 (age when nostalgia peaks based on psychology research)
- Width = 8 (Gaussian curve width)
- Pre-birth Decay Rate = 0.03 (decay rate for pre-birth content)
- Cultural Weight = 0.4 (maximum cultural nostalgia contribution)
- Base Weight = 0.7 (base personal nostalgia weight)
- Popularity Boost = 0.3 (maximum popularity boost)

**Procedure:**

**Step 1: Calculate Age at Release**

1. Compute the user's age when the content was released by subtracting the birth year from the release year.

**Step 2: Calculate Age-Based Nostalgia Score**

1. If the age at release is zero or positive (content released after user's birth):
   - Calculate the age score using the Gaussian formula centered at Peak Age with the specified Width.
   - The score equals the exponential of negative one times the squared difference between the age at release and Peak Age, divided by two times the Width squared.
2. If the age at release is negative (content released before user's birth):
   - First calculate what the score would be at birth using the Gaussian formula with age zero.
   - Then multiply this birth score by an exponential decay factor based on how many years before birth the content was released.
   - The decay factor equals the exponential of negative Pre-birth Decay Rate times the absolute value of the age at release.

**Step 3: Calculate Popularity Score**

1. If the rating count is zero or negative, or the maximum count is zero or negative, set the popularity score to 0.0.
2. If linear scaling is specified:
   - Divide the rating count by the maximum count.
   - Cap the result at 1.0 if it exceeds 1.0.
3. If logarithmic scaling is specified:
   - Calculate the natural logarithm of one plus the rating count.
   - Divide by the natural logarithm of one plus the maximum count.

**Step 4: Calculate Personal Nostalgia Component**

1. Compute the personal nostalgia as the age score multiplied by the sum of Base Weight and Popularity Boost times the popularity score.
2. This ensures popularity boosts but cannot create personal nostalgia.

**Step 5: Calculate Cultural Nostalgia Component**

1. If the age at release is negative (pre-birth content):
   - Set the cultural nostalgia to the popularity score multiplied by Cultural Weight.
2. Otherwise:
   - Set the cultural nostalgia to 0.0.

**Step 6: Combine and Clamp**

1. Sum the personal nostalgia and cultural nostalgia components.
2. Clamp the result to be at least 0.0 and at most 1.0.
3. Round to three decimal places.

**Step 7: Return Score**

1. Return the final nostalgia score.

---

### Algorithm 3a: Age-Based Nostalgia (Sub-procedure)

**Input:**

- `age_at_release`: User's age when content was released (can be negative)

**Output:**

- `score`: Age-based nostalgia score in range [0, 1]

**Constants:**

- Peak Age = 13
- Width = 8
- Pre-birth Decay Rate = 0.03

**Procedure:**

**Step 1: Determine Birth Status**

1. If the age at release is zero or positive (post-birth content):
   - Calculate the score using a Gaussian distribution centered at Peak Age.
   - The maximum score of 1.0 occurs when age at release equals Peak Age.
   - Scores decrease symmetrically as the age deviates from Peak Age.
2. If the age at release is negative (pre-birth content):
   - Calculate the score that would apply at birth (age zero).
   - Apply exponential decay based on how many years before birth the content was released.
   - Older pre-birth content receives progressively lower scores.

**Step 2: Return Score**

1. Return the calculated score.

---

### Algorithm 3b: Popularity Score (Sub-procedure)

**Input:**

- `rating_count`: Number of ratings or popularity metric for this content
- `max_count`: Maximum rating count in the dataset
- `use_linear`: If true, use linear scaling

**Output:**

- `score`: Popularity score in range [0, 1]

**Procedure:**

**Step 1: Validate Input**

1. If the rating count is zero or negative, or the maximum count is zero or negative, return 0.0.

**Step 2: Calculate Score**

1. If linear scaling is specified:
   - Divide the rating count by the maximum count.
   - This is appropriate for pre-normalized metrics such as Spotify's 0-100 popularity score.
2. If logarithmic scaling is specified:
   - Calculate the natural logarithm of one plus the rating count, divided by the natural logarithm of one plus the maximum count.
   - This compresses large values and prevents extremely popular content from dominating.

**Step 3: Return Score**

1. Return the calculated popularity score.

---

## 3. Contextual Bandit Selection Algorithm

The system uses a Hierarchical LinUCB (Linear Upper Confidence Bound) contextual bandit to select optimal content based on the user's current context. The algorithm balances exploitation (recommending content known to evoke nostalgia) with exploration (trying new content to learn user preferences).

### Algorithm 4: Hierarchical Bandit Selection

**Input:**

- `user_id`: Unique identifier for the user
- `context`: Context feature vector containing stress, emotion, history, and birth year information
- `candidates`: List of candidate content items

**Output:**

- `selected_idx`: Index of selected candidate
- `bandit_score`: Confidence score for selection

**Constants:**

- Minimum User Updates = 10 (minimum interactions before using personalized model)
- Maximum Blend Weight = 0.7 (maximum weight for user model)

**Procedure:**

**Step 1: Global Model Selection**

1. Invoke the Global Model's selection procedure with the context and candidates.
2. Store the returned global index and global score.

**Step 2: Check Personalization Eligibility**

1. Retrieve or create the per-user model for this user.
2. If the user model has fewer updates than the Minimum User Updates threshold:
   - Return the global index and global score (cold-start user receives global recommendations).

**Step 3: User Model Selection**

1. Invoke the User Model's selection procedure with the context and candidates.
2. Store the returned user index and user score.

**Step 4: Blend Predictions**

1. Calculate the blend weight as the user model's update count divided by 50, capped at Maximum Blend Weight.
2. Compare the user score multiplied by the blend weight against the global score multiplied by one minus the blend weight.
3. If the weighted user score exceeds the weighted global score:
   - Return the user index and user score.
4. Otherwise:
   - Return the global index and global score.

---

### Algorithm 5: LinUCB Arm Selection

**Input:**

- `context`: Context feature vector
- `candidates`: List of candidate content items

**Output:**

- `selected_idx`: Index of candidate with highest UCB score
- `ucb_score`: Upper confidence bound score

**Procedure:**

**Step 1: Ensure Context Shape**

1. Reshape the context vector to the required dimensions, padding with zeros if necessary or truncating if too long.

**Step 2: Check Model Fitness**

1. If the model has not been fitted with any training data:
   - Select a random index from the candidates.
   - Return the random index with a default score of 0.5.

**Step 3: Map Candidates to Arms**

1. For each candidate in the candidates list:
   - Determine the appropriate genre arm using the genre normalization procedure.
   - Associate the arm with the candidate.

**Step 4: Compute UCB Scores**

1. Initialize an empty list to store index-score pairs.
2. For each candidate and its index:
   - Extract the candidate's genre arm.
   - If the arm is recognized by the model:
     - Query the model for expected reward predictions for all arms given the context.
     - Retrieve the expected reward for this specific arm.
   - If the arm is not recognized:
     - Use a default score of 0.5.
   - Add the index and score pair to the list.

**Step 5: Select Best Arm**

1. Sort the index-score pairs by score in descending order.
2. Extract the index and score of the highest-scoring candidate.

**Step 6: Return Selection**

1. Return the best index and its score.

---

### Algorithm 6: LinUCB Model Update

**Input:**

- `context`: Context feature vector
- `candidate`: The content item that was recommended
- `reward`: Observed reward (1.0 for positive feedback, 0.0 for negative)

**Procedure:**

**Step 1: Prepare Inputs**

1. Reshape the context vector to the required dimensions.
2. Determine the genre arm for the candidate using the genre normalization procedure.
3. Convert the reward to a binary value: 1 if the reward exceeds 0.5, otherwise 0.

**Step 2: Update Model**

1. If the model has not been fitted previously:
   - Perform initial model fitting with the arm decision, binary reward, and context.
   - Mark the model as fitted.
2. If the model has been fitted previously:
   - Perform incremental update (partial fit) with the arm decision, binary reward, and context.

**Step 3: Increment Counter**

1. Add one to the update counter to track the number of learning events.

---

## 4. Context Feature Construction

The context vector encodes the user's current state for the contextual bandit.

### Algorithm 7: Build Context Features

**Input:**

- `stress_score`: Detected stress level (0.0 to 1.0)
- `emotion`: Detected emotion string
- `user_positive_rate`: Historical positive feedback rate (0.0 to 1.0)
- `birth_year`: User's year of birth

**Output:**

- `context`: Feature vector of dimension 12

**Constants:**

- Emotion Categories = ["anger", "fear", "joy", "love", "neutral", "sadness", "surprise"]
- Birth Year Center = 2000
- Birth Year Scale = 40
- Context Dimension = 12

**Procedure:**

**Step 1: Initialize Feature List**

1. Create an empty list to hold feature values.

**Step 2: Add Stress Feature**

1. Append the stress score to the feature list.

**Step 3: Add Emotion One-Hot Encoding**

1. For each emotion in the Emotion Categories list:
   - If the emotion matches the detected emotion, append 1.0.
   - Otherwise, append 0.0.

**Step 4: Add User History Feature**

1. Append the user's positive feedback rate to the feature list.

**Step 5: Add Birth Year Feature**

1. If a birth year is provided:
   - Calculate the normalized birth year by subtracting Birth Year Center from the birth year and dividing by Birth Year Scale.
2. If no birth year is provided:
   - Use 0.0 as the normalized birth year.
3. Append the normalized birth year to the feature list.

**Step 6: Add Padding**

1. While the feature list length is less than Context Dimension:
   - Append 0.0 to the feature list.

**Step 7: Return Features**

1. Return the first Context Dimension elements of the feature list.

---

## 5. Genre Normalization

Genres are normalized to a fixed set of arms for the contextual bandit.

### Algorithm 8: Genre Normalization

**Input:**

- `raw_genre`: Raw genre string (may contain multiple genres separated by "|")
- `content_type`: Either "movie" or "song"

**Output:**

- `normalized`: One of the 12 canonical genre arms

**Procedure:**

**Step 1: Handle Empty Input**

1. If the raw genre is empty or null:
   - If the content type is "movie", return "other_movie".
   - If the content type is "song", return "other_song".

**Step 2: Extract First Genre**

1. Split the raw genre string by the "|" separator.
2. Take the first element from the resulting list.
3. Convert to lowercase and remove leading/trailing whitespace.

**Step 3: Map to Canonical Genre**

1. If the content type is "movie":
   - Look up the first genre in the Movie Genre Map.
   - The map consolidates genres as follows: adventure maps to action, horror/crime/mystery map to thriller, sci-fi/fantasy map to action, animation/family/musical map to comedy, war/history map to drama, and documentary maps to other_movie.
   - If found, return the mapped genre.
   - If not found, return "other_movie".
2. If the content type is "song":
   - Look up the first genre in the Song Genre Map.
   - The map consolidates genres as follows: alternative/indie/metal/punk map to rock, hip-hop/rap map to hiphop, r&b/soul/blues map to rnb, folk maps to country, electronic/dance/edm/latin map to pop, and jazz/classical/reggae map to other_song.
   - If found, return the mapped genre.
   - If not found, return "other_song".

---

## Summary of Algorithm Parameters

| Algorithm           | Parameter               | Default Value | Description                                  |
| ------------------- | ----------------------- | ------------- | -------------------------------------------- |
| Nostalgia Score     | Peak Age                | 13            | Age when nostalgia peaks (reminiscence bump) |
| Nostalgia Score     | Width                   | 8             | Gaussian curve width                         |
| Nostalgia Score     | Pre-birth Decay Rate    | 0.03          | Decay rate for pre-birth content             |
| Nostalgia Score     | Cultural Weight         | 0.4           | Maximum cultural nostalgia contribution      |
| Nostalgia Score     | Minimum Nostalgia Score | 0.3           | Threshold for nostalgic content              |
| LinUCB              | Alpha                   | 1.0           | Exploration parameter                        |
| LinUCB              | Context Dimension       | 12            | Number of context features                   |
| Hierarchical Bandit | Minimum User Updates    | 10            | Interactions before personalization          |
| Hierarchical Bandit | Maximum Blend Weight    | 0.7           | Maximum personalization weight               |
| Recommender         | Maximum Movie Ratings   | 100,000       | Normalization constant for movie popularity  |
| Recommender         | Maximum Song Popularity | 100           | Normalization constant for song popularity   |

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
