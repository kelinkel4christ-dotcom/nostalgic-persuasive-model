"""
Contextual Bandit for Nostalgic Recommendations using MAB2Rec.

This module implements a contextual bandit using the mab2rec library
with LinUCB policy for selecting optimal nostalgic content recommendations.

The bandit learns which content features work best in different
contexts (stress level, emotion, time of day, etc.).
Models are stored in PostgreSQL for persistence.
"""

import io
import json
import math
import os
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, ItemsView, Literal

import joblib
import numpy as np
from mabwiser.mab import MAB, LearningPolicy

import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from core.db import get_db_connection


# Type aliases
ContentType = Literal["song", "movie"]

# Default context dimension
# Components: stress(1) + emotion(7) + positive_rate(1) + birth_year(1) + padding(2) = 12
CONTEXT_DIM = 12

# Default cache settings
DEFAULT_CACHE_SIZE = 500
DEFAULT_FLUSH_THRESHOLD = 10


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache with eviction callback.

    When the cache exceeds max_size, the least recently used item is evicted
    and the on_evict callback is called to allow persistence before removal.
    """

    def __init__(
        self,
        max_size: int,
        on_evict: Callable[[str, Any], None] | None = None,
    ) -> None:
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to keep in cache.
            on_evict: Callback called with (key, value) before eviction.
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.on_evict = on_evict

    def get(self, key: str) -> Any | None:
        """Get item from cache, marking it as recently used."""
        if key in self.cache:
            self.cache.move_to_end(key)  # Mark as recently used
            return self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set item in cache, evicting oldest if over capacity."""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value

        # Evict oldest if over capacity
        while len(self.cache) > self.max_size:
            oldest_key, oldest_value = self.cache.popitem(last=False)
            if self.on_evict:
                self.on_evict(oldest_key, oldest_value)

    def items(self) -> ItemsView[str, Any]:
        """Return all items in cache."""
        return self.cache.items()

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self.cache

    def __len__(self) -> int:
        """Return number of items in cache."""
        return len(self.cache)


class LinUCBBandit:
    """
    LinUCB contextual bandit using MABWiser.

    LinUCB maintains a linear model for each arm and uses upper confidence
    bounds for exploration. It learns the relationship between context
    features and rewards for each arm (content type/genre).
    """

    def __init__(
        self,
        arms: list[str] | None = None,
        alpha: float = 1.0,
        context_dim: int = CONTEXT_DIM,
    ) -> None:
        """
        Initialize the LinUCB bandit.

        Args:
            arms: List of arm identifiers (e.g., content types/genres).
            alpha: Exploration parameter (higher = more exploration).
            context_dim: Number of context features.
        """
        # Default arms: genre-only (12 total)
        # Genre implicitly identifies content type (movie genres vs song genres don't overlap)
        if arms is None:
            movie_genres = [
                "drama",
                "comedy",
                "action",
                "romance",
                "thriller",
                "other_movie",
            ]
            song_genres = ["pop", "rock", "hiphop", "rnb", "country", "other_song"]
            arms = movie_genres + song_genres

        self.arms = arms
        self.alpha = alpha
        self.context_dim = context_dim
        self.n_updates = 0

        # Initialize MABWiser with LinUCB policy
        self.mab = MAB(
            arms=arms,
            learning_policy=LearningPolicy.LinUCB(alpha=alpha),
        )

        # Track if we have any training data
        self._is_fitted = False

    def _get_arm_from_candidate(self, candidate: dict) -> str:
        """Map a candidate to its genre arm."""
        content_type = candidate.get("type", "movie")

        if content_type == "movie":
            raw_genre = candidate.get("genres", "")
            return normalize_movie_genre(raw_genre)
        else:
            raw_genre = candidate.get("genre", "")
            return normalize_song_genre(raw_genre)

    def _ensure_context_shape(self, context: np.ndarray) -> np.ndarray:
        """Ensure context has the right shape."""
        context = np.array(context).flatten()
        if len(context) < self.context_dim:
            context = np.pad(context, (0, self.context_dim - len(context)))
        elif len(context) > self.context_dim:
            context = context[: self.context_dim]
        return context.reshape(1, -1)

    def select(
        self,
        context: np.ndarray,
        candidates: list[dict],
    ) -> tuple[int, float]:
        """
        Select the best candidate using LinUCB.

        Args:
            context: Context feature vector.
            candidates: List of candidate content items.

        Returns:
            Tuple of (selected_index, score).
        """
        if not candidates:
            raise ValueError("No candidates provided")

        context_2d = self._ensure_context_shape(context)

        # If not fitted yet, select randomly
        if not self._is_fitted:
            import random

            idx = random.randint(0, len(candidates) - 1)
            return idx, 0.5

        # Map candidates to arms
        candidate_arms = [self._get_arm_from_candidate(c) for c in candidates]

        # Get prediction from MAB for each candidate's arm
        scores = []
        for i, arm in enumerate(candidate_arms):
            if arm in self.arms:
                # Get expectation for this arm given context
                expectations = self.mab.predict_expectations(context_2d)
                # Handle list return type (mabwiser returns list for 2D input)
                if isinstance(expectations, list):
                    expectations = expectations[0]
                score = expectations.get(arm, 0.5)
            else:
                score = 0.5
            scores.append((i, score))

        # Sort by score and return best
        scores.sort(key=lambda x: x[1], reverse=True)
        best_idx, best_score = scores[0]

        return best_idx, float(best_score)

    def update(
        self,
        context: np.ndarray,
        candidate: dict,
        reward: float,
    ) -> None:
        """
        Update the bandit with observed reward.

        Args:
            context: Context feature vector.
            candidate: The candidate that was shown.
            reward: Observed reward (0-1).
        """
        context_2d = self._ensure_context_shape(context)
        arm = self._get_arm_from_candidate(candidate)

        # Use continuous reward directly
        decision = arm

        if not self._is_fitted:
            # First fit
            self.mab.fit(
                decisions=[decision],
                rewards=[reward],
                contexts=context_2d,
            )
            self._is_fitted = True
        else:
            # Incremental update
            self.mab.partial_fit(
                decisions=[decision],
                rewards=[reward],
                contexts=context_2d,
            )

        self.n_updates += 1

    def warm_start(
        self, decisions: list[str], rewards: list[float], contexts: np.ndarray
    ) -> None:
        """
        Warm start the bandit with historical data.

        Args:
            decisions: List of arm decisions.
            rewards: List of rewards.
            contexts: Context matrix (n_samples, context_dim).
        """
        if len(decisions) == 0:
            return

        self.mab.fit(
            decisions=decisions,
            rewards=rewards,
            contexts=contexts,
        )
        self._is_fitted = True
        self.n_updates = len(decisions)

    def serialize(self) -> bytes:
        """Serialize the bandit model to bytes."""
        data = {
            "arms": self.arms,
            "alpha": self.alpha,
            "context_dim": self.context_dim,
            "n_updates": self.n_updates,
            "is_fitted": self._is_fitted,
            "mab": self.mab if self._is_fitted else None,
        }
        buffer = io.BytesIO()
        joblib.dump(data, buffer)
        buffer.seek(0)
        return buffer.read()

    @classmethod
    def deserialize(cls, data: bytes) -> "LinUCBBandit":
        """Deserialize a bandit model from bytes."""
        buffer = io.BytesIO(data)
        loaded_data = joblib.load(buffer)
        bandit = cls(
            arms=loaded_data["arms"],
            alpha=loaded_data["alpha"],
            context_dim=loaded_data["context_dim"],
        )
        bandit.n_updates = loaded_data.get("n_updates", 0)
        bandit._is_fitted = loaded_data.get("is_fitted", False)
        if loaded_data.get("mab") is not None:
            bandit.mab = loaded_data["mab"]
        return bandit

    def to_dict(self) -> dict:
        """Serialize bandit state (metadata only, for backward compat)."""
        return {
            "arms": self.arms,
            "alpha": self.alpha,
            "context_dim": self.context_dim,
            "n_updates": self.n_updates,
            "is_fitted": self._is_fitted,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LinUCBBandit":
        """Create bandit from dict (metadata only, no model weights)."""
        bandit = cls(
            arms=data["arms"],
            alpha=data["alpha"],
            context_dim=data["context_dim"],
        )
        bandit.n_updates = data.get("n_updates", 0)
        bandit._is_fitted = data.get("is_fitted", False)
        return bandit


class HierarchicalBandit:
    """
    Hierarchical bandit with global and per-user LinUCB models.

    - Global model learns from all users
    - Per-user models refine predictions for individual users
    - Blends predictions based on user's feedback history

    Models are stored in PostgreSQL for persistence.
    User models are cached in an LRU cache with configurable size.
    Persistence is batched to reduce DB load.
    """

    def __init__(
        self,
        alpha: float = 1.0,
        min_user_updates: int = 10,
        cache_size: int = DEFAULT_CACHE_SIZE,
        flush_threshold: int = DEFAULT_FLUSH_THRESHOLD,
    ) -> None:
        """
        Initialize hierarchical bandit.

        Args:
            alpha: LinUCB exploration parameter.
            min_user_updates: Minimum updates before using per-user model.
            cache_size: Maximum number of user models to keep in memory.
            flush_threshold: Number of updates before flushing dirty models to DB.
        """
        self.alpha = alpha
        self.min_user_updates = min_user_updates
        self.flush_threshold = flush_threshold

        # Global model (always in memory)
        self.global_model = self._load_global_from_db()

        # LRU cache for user models (saves to DB on eviction)
        self.user_models: LRUCache = LRUCache(
            max_size=cache_size,
            on_evict=self._on_user_evict,
        )

        # Dirty tracking for batched persistence
        self._dirty_users: set[str] = set()
        self._dirty_global: bool = False
        self._update_count: int = 0

        print(f"   Cache size: {cache_size}, flush threshold: {flush_threshold}")

    def _save_to_db(self, model_id: str, bandit: LinUCBBandit) -> None:
        """Save a bandit model to the database (base64 encoded)."""
        import base64

        model_data = base64.b64encode(bandit.serialize()).decode("utf-8")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO bandit_models (model_id, model_data, n_updates, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (model_id) 
                DO UPDATE SET model_data = EXCLUDED.model_data, 
                              n_updates = EXCLUDED.n_updates, 
                              updated_at = EXCLUDED.updated_at
            """,
                (model_id, model_data, bandit.n_updates, datetime.utcnow()),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def _load_from_db(self, model_id: str) -> LinUCBBandit | None:
        """Load a bandit model from the database (base64 decoded)."""
        import base64

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT model_data, n_updates 
                FROM bandit_models 
                WHERE model_id = %s
            """,
                (model_id,),
            )
            row = cursor.fetchone()
            if row:
                model_data_b64, n_updates = row
                model_data = base64.b64decode(model_data_b64)
                bandit = LinUCBBandit.deserialize(model_data)
                bandit.n_updates = n_updates
                return bandit
            return None
        finally:
            cursor.close()
            conn.close()

    def _load_global_from_db(self) -> LinUCBBandit:
        """Load global model from DB or create new one."""
        bandit = self._load_from_db("global")
        if bandit:
            print(f"   Loaded global bandit from DB with {bandit.n_updates} updates")
            return bandit
        print("   Creating new global bandit")
        return LinUCBBandit(alpha=self.alpha)

    def _load_user_from_db(self, user_id: str) -> LinUCBBandit | None:
        """Load user model from DB."""
        return self._load_from_db(f"user_{user_id}")

    def _on_user_evict(self, user_id: str, model: LinUCBBandit) -> None:
        """
        Called when a user model is evicted from LRU cache.

        Saves the model to DB before eviction to preserve learned state.

        Args:
            user_id: User identifier.
            model: The LinUCBBandit being evicted.
        """
        try:
            self._save_to_db(f"user_{user_id}", model)
            # Remove from dirty set since it's now persisted
            self._dirty_users.discard(user_id)
        except Exception as e:
            print(f"Error saving evicted user model {user_id}: {e}")

    def get_user_model(self, user_id: str) -> LinUCBBandit:
        """
        Get or create per-user model (uses LRU cache).

        Args:
            user_id: User identifier.

        Returns:
            LinUCBBandit for this user.
        """
        # Check cache first
        cached = self.user_models.get(user_id)
        if cached is not None:
            return cached

        # Try load from DB
        loaded = self._load_user_from_db(user_id)
        if loaded:
            self.user_models.set(user_id, loaded)
            return loaded

        # Create new
        new_model = LinUCBBandit(alpha=self.alpha)
        self.user_models.set(user_id, new_model)
        return new_model

    def select(
        self,
        user_id: str,
        context: np.ndarray,
        candidates: list[dict],
    ) -> tuple[int, float]:
        """
        Select the best candidate using hierarchical bandit.

        Args:
            user_id: User identifier.
            context: Context feature vector.
            candidates: List of candidate content items.

        Returns:
            Tuple of (selected_index, bandit_score).
        """
        if not candidates:
            raise ValueError("No candidates provided")

        # Try global model first
        try:
            global_idx, global_score = self.global_model.select(context, candidates)
        except Exception as e:
            print(f"Global model selection error: {e}")
            import random

            return random.randint(0, len(candidates) - 1), 0.5

        # Get user model
        user_model = self.get_user_model(user_id)

        # Blend if user has enough history
        if user_model.n_updates >= self.min_user_updates:
            try:
                user_idx, user_score = user_model.select(context, candidates)

                # Calculate blend weight
                blend = min(user_model.n_updates / 50, 0.7)

                # Use weighted selection
                if user_score * blend > global_score * (1 - blend):
                    return user_idx, user_score
            except Exception:
                pass

        return global_idx, global_score

    def update(
        self,
        user_id: str,
        context: np.ndarray,
        candidate: dict,
        reward: float,
    ) -> None:
        """
        Update both global and per-user models with reward.

        Uses batched persistence to reduce DB load. Models are marked dirty
        and flushed to DB every flush_threshold updates.

        Args:
            user_id: User identifier.
            context: Context feature vector.
            candidate: The candidate that was shown.
            reward: Observed reward (0-1).
        """
        # Update global model
        try:
            self.global_model.update(context, candidate, reward)
            self._dirty_global = True
        except Exception as e:
            print(f"Global model update error: {e}")

        # Update per-user model
        try:
            user_model = self.get_user_model(user_id)
            user_model.update(context, candidate, reward)
            self._dirty_users.add(user_id)
        except Exception as e:
            print(f"User model update error: {e}")

        # Increment counter and maybe flush
        self._update_count += 1
        if self._update_count >= self.flush_threshold:
            self._flush_dirty()

    def _flush_dirty(self) -> None:
        """
        Persist all dirty models to DB.

        Called automatically every flush_threshold updates,
        on LRU eviction, and on shutdown.
        """
        # Flush global if dirty
        if self._dirty_global:
            try:
                self._save_to_db("global", self.global_model)
                self._dirty_global = False
            except Exception as e:
                print(f"Error saving global model: {e}")

        # Flush dirty users
        for user_id in list(self._dirty_users):
            cached = self.user_models.get(user_id)
            if cached is not None:
                try:
                    self._save_to_db(f"user_{user_id}", cached)
                    self._dirty_users.discard(user_id)
                except Exception as e:
                    print(f"Error saving user {user_id} model: {e}")

        self._update_count = 0

    def warm_start_user(
        self,
        user_id: str,
        selected_items: list[dict],
        context: np.ndarray | None = None,
    ) -> None:
        """
        Warm-start user model with onboarding selections.

        Args:
            user_id: User identifier.
            selected_items: List of items user selected during onboarding.
            context: Optional context (uses neutral context if not provided).
        """
        if not selected_items:
            return

        if context is None:
            # Neutral context
            context = np.zeros(CONTEXT_DIM)
            context[0] = 0.3  # Neutral stress
            context[5] = 1.0  # Neutral emotion

        user_model = self.get_user_model(user_id)

        # Build training data from selections
        decisions = []
        rewards = []
        contexts = []

        for item in selected_items:
            arm = user_model._get_arm_from_candidate(item)
            decisions.append(arm)
            rewards.append(1)  # Selection = positive
            contexts.append(context)

        if decisions:
            contexts_array = np.array(contexts)
            user_model.warm_start(decisions, rewards, contexts_array)
            # Warm start is important, save immediately
            self._save_to_db(f"user_{user_id}", user_model)
            self._dirty_users.discard(user_id)  # Just saved, not dirty

    def close(self) -> None:
        """
        Save all models and clean up.

        Flushes all dirty models to DB and saves any remaining cached models.
        Should be called on server shutdown.
        """
        # First, flush all dirty models
        self._flush_dirty()

        # Then save any remaining cached models (safety net)
        for user_id, model in self.user_models.items():
            try:
                self._save_to_db(f"user_{user_id}", model)
            except Exception as e:
                print(f"Error saving user {user_id} on close: {e}")

        # Clear dirty tracking
        self._dirty_users.clear()
        self._dirty_global = False


def build_context_features(
    stress_score: float,
    emotion: str,
    birth_year: int | None = None,
    user_positive_rate: float = 0.5,
) -> np.ndarray:
    """
    Build context feature vector from user state.

    Args:
        stress_score: Stress level (0-1).
        emotion: Detected emotion.
        birth_year: User's birth year (for age-based context).
        user_positive_rate: User's historical positive feedback rate.

    Returns:
        Context feature vector (12 dimensions).
    """
    features = []

    # Stress (1 feature)
    features.append(stress_score)

    # Emotion one-hot (7 features)
    emotions = ["anger", "fear", "joy", "love", "neutral", "sadness", "surprise"]
    for e in emotions:
        features.append(1.0 if emotion == e else 0.0)

    # User's historical positive rate (1 feature)
    features.append(user_positive_rate)

    # Birth Year (Normalized) (1 feature)
    # Normalize around 2000 with a scale of 40 years (range ~1960-2040)
    if birth_year:
        norm_birth_year = (birth_year - 2000) / 40.0
    else:
        norm_birth_year = 0.0  # Default to 2000
    features.append(norm_birth_year)

    # Pad to CONTEXT_DIM
    while len(features) < CONTEXT_DIM:
        features.append(0.0)

    return np.array(features[:CONTEXT_DIM], dtype=np.float32)


def calculate_reward(
    interaction_type: str = "feedback",
    brings_back_memories: bool | None = None,
    duration_seconds: int = 0,
    feedback_submitted: bool = False,
) -> float | None:
    """
    Calculate reward from user feedback and interaction signals.

    Reward Hierarchy:
    1. Explicit Feedback (Yes/No) - Overrides everything
    2. Replay (1.0) - Strong positive
    3. Click (0.8) - Positive interest
    4. Passive View > 30s (0.6) - Mild interest (only if no explicit feedback)
    5. Skip (0.0) - Negative

    Args:
        interaction_type: Type of interaction (view, click, skip, next, replay, feedback)
        brings_back_memories: Explicit feedback signal (if present)
        duration_seconds: Duration of interaction
        feedback_submitted: Whether explicit feedback was already submitted

    Returns:
        Reward (0-1) or None if interaction should be ignored
    """
    # 1. Explicit Feedback (Gold Standard)
    # If user explicitly answers "Yes" or "No", this is the definitive signal.
    if brings_back_memories is not None:
        return 1.0 if brings_back_memories else 0.0

    # 2. Strong Implicit Signals
    if interaction_type == "replay":
        return 1.0

    if interaction_type == "click":
        return 0.8

    # 3. Passive Engagement
    # "next" implies they finished looking at it.
    if interaction_type == "next":
        # If they lingered > 30s and haven't already voted, count as mild positive.
        # If they already voted, we ignore the "next" event to avoid double-counting or diluting.
        if duration_seconds > 30 and not feedback_submitted:
            return 0.6
        return None

    # 4. Negative Signals
    if interaction_type == "skip":
        return 0.0

    # Ignore 'view' (just an impression) and other unknown types
    return None


# =============================================================================
# Genre Normalization
# =============================================================================

MOVIE_GENRE_MAP: dict[str, str] = {
    "drama": "drama",
    "comedy": "comedy",
    "action": "action",
    "adventure": "action",
    "romance": "romance",
    "thriller": "thriller",
    "horror": "thriller",
    "crime": "thriller",
    "sci-fi": "action",
    "science fiction": "action",
    "animation": "comedy",
    "family": "comedy",
    "fantasy": "action",
    "mystery": "thriller",
    "war": "drama",
    "western": "action",
    "documentary": "other_movie",
    "musical": "comedy",
    "history": "drama",
}

SONG_GENRE_MAP: dict[str, str] = {
    "pop": "pop",
    "rock": "rock",
    "alternative": "rock",
    "indie": "rock",
    "hip hop": "hiphop",
    "hip-hop": "hiphop",
    "rap": "hiphop",
    "r&b": "rnb",
    "rnb": "rnb",
    "soul": "rnb",
    "country": "country",
    "folk": "country",
    "blues": "rnb",
    "electronic": "pop",
    "dance": "pop",
    "edm": "pop",
    "jazz": "other_song",
    "classical": "other_song",
    "metal": "rock",
    "punk": "rock",
    "reggae": "other_song",
    "latin": "pop",
}


def normalize_movie_genre(raw: str) -> str:
    """Normalize movie genre to one of 6 categories."""
    if not raw:
        return "other_movie"
    # Handle both string and list formats
    if isinstance(raw, list):
        first_genre = raw[0].lower().strip() if raw else ""
    else:
        first_genre = str(raw).split("|")[0].lower().strip()
    return MOVIE_GENRE_MAP.get(first_genre, "other_movie")


def normalize_song_genre(raw: str) -> str:
    """Normalize song genre to one of 6 categories."""
    if not raw:
        return "other_song"
    genre = str(raw).lower().strip()
    return SONG_GENRE_MAP.get(genre, "other_song")


# =============================================================================
# Nostalgia Scoring
# =============================================================================


def age_nostalgia(
    age_at_release: int,
    peak_age: float = 13.0,
    width: float = 8.0,
    prebirth_decay: float = 0.03,
) -> float:
    """
    Age-based nostalgia score.

    - Post-birth: Gaussian centered at peak_age (reminiscence bump)
    - Pre-birth: Exponential decay from birth point

    Args:
        age_at_release: User's age when content was released (can be negative)
        peak_age: Peak nostalgia age (default 13, based on psychology research)
        width: Gaussian width (default 8)
        prebirth_decay: Decay rate for pre-birth content (default 0.03)

    Returns:
        Age nostalgia score (0-1)
    """
    if age_at_release >= 0:
        return math.exp(-((age_at_release - peak_age) ** 2) / (2 * width**2))
    else:
        birth_score = math.exp(-((0 - peak_age) ** 2) / (2 * width**2))
        return birth_score * math.exp(-prebirth_decay * abs(age_at_release))


def popularity_score(rating_count: float, max_count: float) -> float:
    """
    Log-scaled popularity score to prevent mega-hits from dominating.

    Args:
        rating_count: Number of ratings for this content
        max_count: Maximum rating count in dataset

    Returns:
        Popularity score (0-1)
    """
    if rating_count <= 0 or max_count <= 0:
        return 0.0
    return math.log1p(rating_count) / math.log1p(max_count)


def nostalgia_score(
    birth_year: int,
    release_year: int,
    rating_count: float,
    max_count: float,
    use_linear: bool = False,
    target_period: tuple[int, int] | None = None,
) -> float:
    """
    Combined nostalgia score. Popularity BOOSTS but cannot CREATE nostalgia.

    Formula: personal * (0.7 + 0.3 * pop) + cultural
    - personal: age-based nostalgia (lived experience)
    - cultural: popularity boost for pre-birth content (inherited memory)

    Note: Recency filtering (10-year minimum) is handled at the recommender level,
    so all content passed here is already guaranteed to be old enough.

    Args:
        birth_year: User's birth year
        release_year: Content release year
        rating_count: Number of ratings for this content
        max_count: Maximum rating count in dataset
        use_linear: If True, use linear scaling (value/max) instead of log scaling.
                    Use for pre-normalized scores like Spotify popularity (0-100).
        target_period: Optional (start_year, end_year) tuple for explicit user preference.
                       If provided, peak nostalgia is centered on this period.

    Returns:
        Nostalgia score (0-1)
    """
    if target_period:
        # User defined a specific period: Center Gaussian on the middle of that period
        start, end = target_period
        mid_year = (start + end) / 2
        # Distance from target center
        dist = abs(release_year - mid_year)

        # Width should cover the range. Range is end - start. Sigma approx range/2
        width = max(5.0, (end - start) / 2.0)

        # Gaussian score
        personal = math.exp(-(dist**2) / (2 * width**2))

        # Cultural boost is less relevant here
        cultural = 0.0
    else:
        # Default: Use Reminiscence Bump (Age 13)
        age_at_release = release_year - birth_year
        personal = age_nostalgia(age_at_release)
        cultural = 0.0

        # Cultural boost for pre-birth content if NOT using target period
        if use_linear:
            pop_score = min(1.0, rating_count / max_count) if max_count > 0 else 0.0
        else:
            pop_score = popularity_score(rating_count, max_count)

        if age_at_release < 0:
            cultural = pop_score * 0.4

    # Calculate popularity score (needed for both paths)
    if use_linear:
        pop_score = min(1.0, rating_count / max_count) if max_count > 0 else 0.0
    else:
        pop_score = popularity_score(rating_count, max_count)

    # Final score: popularity boosts but doesn't create nostalgia
    final = personal * (0.7 + 0.3 * pop_score) + cultural

    return round(min(1.0, max(0.0, final)), 3)
