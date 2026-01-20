# Feedback Loop

This section describes the feedback loop of the Nostalgic Persuasive Recommendation System, explaining how user responses drive the reinforcement learning process that continuously improves recommendation quality.

## Overview

After viewing a recommended piece of content (song or movie), the participant is prompted with the question: "Does this bring back memories?" Their response serves as the reward signal for the contextual bandit algorithm, enabling the system to learn which content types best evoke nostalgia for each individual user.

## System Components

| Component             | Technology       | Role                                              |
| --------------------- | ---------------- | ------------------------------------------------- |
| Application           | Nuxt.js Frontend | Captures user feedback via UI                     |
| Recommendation Engine | FastAPI          | Processes feedback and coordinates update         |
| Contextual Bandit     | LinUCB           | Learns from feedback to improve future selections |
| Database              | PostgreSQL       | Persists interaction history for analysis         |

## Step-by-Step Flow

**Step 1: User Provides Feedback**
After viewing the recommended content, the participant responds to the nostalgia prompt by selecting either a positive (👍 "Yes, this brings back memories") or negative (👎 "No") response through the application interface.

**Step 2: Submit Feedback**
The Application sends the feedback to the Recommendation Engine, including:

- User ID
- Content ID and type (song or movie)
- Content metadata (year, genre)
- The user's response (positive or negative)

**Step 3: Store Interaction**
The Recommendation Engine persists the interaction to the database, recording:

- `user_id`: The participant who viewed the content
- `content_id`: The specific song or movie that was recommended
- `reward`: Binary value (1 for positive, 0 for negative)
- `context`: The emotional context at the time of recommendation (stress level, emotion)

This stored data enables offline analysis of recommendation effectiveness across the study population.

**Step 4: Partial Fit**
The Recommendation Engine triggers an online learning update on the Contextual Bandit. The reward signal is defined as:

$$r = \begin{cases} 1 & \text{if user responds "brings back memories"} \\ 0 & \text{otherwise} \end{cases}$$

**Steps 5-7: LinUCB Model Update**
The LinUCB algorithm performs three mathematical operations to incorporate the new observation. For the selected arm $a$ and observed context vector $x$:

**Step 5 - Update A matrix:**
$$A_a \leftarrow A_a + x x^T$$

The matrix $A_a$ accumulates the outer product of context vectors, representing the covariance structure of observed contexts for arm $a$. This tracks "how much have we seen this type of context?"

**Step 6 - Update b vector:**
$$b_a \leftarrow b_a + r \cdot x$$

The vector $b_a$ accumulates the reward-weighted context vectors. This captures "how much reward came from this context pattern?"

**Step 7 - Recalculate θ:**
$$\theta_a = A_a^{-1} b_a$$

The weight vector $\theta_a$ is the ridge regression solution representing the model's current best linear estimate of expected reward given context. This answers "what is the expected reward for arm $a$ in context $x$?"

**Step 8: Weights Updated**
The bandit confirms the model update is complete. Both the global model (shared across all users) and the per-user model (personalized) receive this update.

**Steps 9-10: Confirmation**
The Recommendation Engine sends confirmation back through the Application to the User, indicating their feedback has been recorded.

## Mathematical Foundation

### LinUCB Algorithm

The LinUCB (Linear Upper Confidence Bound) algorithm is a contextual bandit method that assumes the expected reward is a linear function of the context:

$$\mathbb{E}[r | x, a] = \theta_a^T x$$

Where:

- $x \in \mathbb{R}^d$ is the context vector (stress, emotion, positive rate, birth year)
- $\theta_a \in \mathbb{R}^d$ is the unknown weight vector for arm $a$
- $r \in \{0, 1\}$ is the observed reward

### Arm Selection (UCB Score)

During recommendation, the algorithm selects the arm with the highest Upper Confidence Bound:

$$a^* = \arg\max_a \left( \theta_a^T x + \alpha \sqrt{x^T A_a^{-1} x} \right)$$

Where:

- $\theta_a^T x$ is the **exploitation term** (expected reward based on learned weights)
- $\alpha \sqrt{x^T A_a^{-1} x}$ is the **exploration bonus** (uncertainty in the estimate)
- $\alpha$ is the exploration parameter (set to 1.0 in our implementation)

The exploration bonus is larger when:

- The context $x$ is dissimilar to previously observed contexts
- Arm $a$ has fewer observations

### Online Learning Properties

The partial fit update has several desirable properties:

1. **O(d²) time complexity**: Each update is efficient, requiring only matrix addition and inversion
2. **No replay buffer**: New observations are incorporated immediately without storing all historical data
3. **Convergence guarantee**: As observations grow, $\theta_a$ converges to the true linear relationship

### Hierarchical Extension

Our implementation extends LinUCB with a hierarchical structure:

$$\theta_{user} = \beta \cdot \theta_{global} + (1 - \beta) \cdot \theta_{local}$$

Where:

- $\theta_{global}$ captures population-level patterns
- $\theta_{local}$ captures user-specific deviations
- $\beta$ decreases as the user accumulates more feedback

This enables new users to benefit from global learning while allowing personalization over time.

## Learning Dynamics

### Immediate Effect

Each piece of feedback immediately influences future recommendations. If a user responds positively to nostalgic movies when stressed, the bandit increases its preference for recommending movies in similar emotional contexts.

### Exploration-Exploitation Balance

The exploration bonus $\alpha \sqrt{x^T A_a^{-1} x}$ naturally balances:

- **Exploitation**: When $A_a$ is large (many observations), the bonus shrinks, favoring the learned preference
- **Exploration**: When $A_a$ is small (few observations), the bonus grows, encouraging exploration

### Convergence Behavior

As more feedback accumulates:

- $A_a$ grows → $A_a^{-1}$ shrinks → exploration bonus decreases
- $\theta_a$ stabilizes → exploitation dominates
- Recommendations become more predictable and aligned with user preferences

## Data Persistence

All feedback interactions are permanently stored in the `content_feedback` table, enabling:

- Offline analysis of recommendation effectiveness
- Comparison between treatment and control groups
- Research insights into nostalgia-emotion relationships
- Model retraining if needed
