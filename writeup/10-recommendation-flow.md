# Recommendation Flow and Feedback Loop

This section describes the recommendation pipeline of the Nostalgic Persuasive Recommendation System, explaining how personalized nostalgic content is generated for participants.

## Recommendation Flow

The recommendation flow is a multi-stage pipeline involving seven system components that work together to deliver contextually-appropriate nostalgic content.

### System Components

| Component             | Technology           | Role                                           |
| --------------------- | -------------------- | ---------------------------------------------- |
| Application           | Nuxt.js Frontend     | User interface for requests and display        |
| Recommendation Engine | FastAPI              | Pipeline orchestrator                          |
| Stress Detection      | RoBERTa (fine-tuned) | Analyzes journal text for stress levels        |
| Emotion Detection     | DistilRoBERTa        | Classifies emotional state from text           |
| Contextual Bandit     | LinUCB               | Selects optimal content based on context       |
| Content Embeddings    | pgvector             | Stores and queries content similarity vectors  |
| Database              | PostgreSQL           | Persists user preferences and content metadata |

### Step-by-Step Flow

**1. User Request**
The participant initiates a recommendation request through the application interface.

**2-4. User Context Retrieval**
The Recommendation Engine queries the database to fetch:

- User preferences (birth year, experiment group)
- Previously liked movies and songs (from onboarding and positive feedback history)
- Latest habit log (most recent stress level and emotion)

**5-11. Real-Time Text Analysis** _(conditional)_
If the participant has submitted a journal entry with their daily check-in, the system performs real-time NLP analysis:

- **Stress Detection (Steps 7-9)**: The journal text is sent to a RoBERTa model fine-tuned for mental health stress detection. The model tokenizes the input, encodes it through transformer layers, and outputs a continuous stress score between 0.0 (calm) and 1.0 (highly stressed).

- **Emotion Detection (Steps 10-11)**: The same text is analyzed by a DistilRoBERTa model trained for emotion classification. The model outputs probability scores across seven emotion categories (anger, fear, joy, love, neutral, sadness, surprise), with the highest-probability emotion returned as the dominant emotional state.

**12-17. Candidate Generation**
The system generates content candidates using similarity-based retrieval with a **10-year recency filter** applied at the database level:

- **Movie Candidates**: The hybrid recommender (LightFM) generates ~50 movies similar to those the participant has previously liked, using matrix factorization with item features. Only movies released 10+ years ago are considered.

- **Song Candidates**: The content-based recommender queries pgvector for ~50 songs with audio feature embeddings similar to the participant's liked songs. Only songs released 10+ years ago are considered.

**18-19. Nostalgia Scoring**
Each candidate receives a **nostalgia score** (0-1) that measures how likely the content is to evoke nostalgic feelings for this specific user. The score combines two factors:

1. **Personal Nostalgia**: Based on the user's age when the content was released. Content experienced during formative years (ages 10-22, the "reminiscence bump") scores highest.

2. **Cultural Nostalgia**: For pre-birth content, popular items receive a boost representing "inherited memory" (classics heard from parents, cultural touchstones).

The formula:

```
Final Score = personal × (0.7 + 0.3 × popularity) + cultural
```

Candidates with low nostalgia scores are filtered out, ensuring only meaningfully nostalgic content proceeds to selection.

**20-24. Contextual Bandit Selection**
The filtered candidates are passed to the LinUCB contextual bandit for final selection:

- **Context Vector Construction (Step 21)**: A feature vector is built containing:
  - Current stress level (0-1)
  - Emotion encoding (one-hot vector)
  - User's historical positive feedback rate
  - Normalized birth year

- **UCB Score Computation (Step 22)**: For each candidate arm (grouped by content type and genre), the bandit computes an Upper Confidence Bound score that balances expected reward against exploration bonus.

- **Exploration vs Exploitation (Step 23)**: The algorithm selects the arm with the highest UCB score, naturally balancing between exploiting known preferences and exploring uncertain options.

- **Within-Arm Selection (Step 24)**: To ensure variety, the system randomly selects from the top 5 highest-similarity candidates within the chosen arm, rather than always returning the same top item.

**25-26. Response Delivery**
The Recommendation Engine returns the selected content to the Application, which displays the recommendation to the participant.

## Feedback Loop

After viewing the recommendation, the participant responds to the prompt "Does this bring back memories?" This feedback drives the reinforcement learning cycle:

1. **Reward Signal**: Positive response = reward of 1; Negative response = reward of 0
2. **Database Storage**: The interaction (user, content, reward, context) is persisted
3. **Bandit Update**: LinUCB performs online learning, updating its weight matrices for both the global model and the user-specific model
4. **Future Impact**: Subsequent recommendations incorporate the learned preference

The feedback loop enables continuous personalization—the system learns which content types and genres best evoke nostalgia for each participant under different emotional contexts.

## Key Implementation Details

### Recency Filter vs Nostalgia Score

The system applies two levels of filtering:

1. **Recency Filter (10-year minimum)**: Applied at the database/recommender level. Ensures all content is old enough to potentially be nostalgic. This is a hard filter—no recent content can pass.

2. **Nostalgia Score**: Applied after candidate generation. Ensures content is personally relevant to this user's age and formative period. This is a soft filter—if no candidates pass, all 10+ year old content is used.

### Stochastic Selection

To prevent repetitive recommendations, the system introduces randomness at two points:

- Candidates are shuffled before bandit selection to prevent positional bias
- Within-arm selection picks randomly from top 5 candidates rather than always choosing #1

### Hierarchical Learning

The bandit maintains two model levels:

- **Global Model**: Learns patterns from all users (e.g., "stressed users prefer movies")
- **Per-User Model**: Personalizes for individual preferences over time

New users benefit from global patterns immediately, while returning users receive increasingly personalized recommendations.
