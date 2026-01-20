"""
Unified Recommendation API Routes.

This module provides the main recommendation endpoint that:
1. Analyzes journal text for stress/emotion
2. Generates candidates from movie and song recommenders
3. Uses contextual bandit to select optimal recommendation
4. Returns the selected content with analysis results
"""

import os

import psycopg2
import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from services.contextual_bandit import (
    HierarchicalBandit,
    build_context_features,
    calculate_reward,
    nostalgia_score,
)
from core.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    EmotionResult,
    RecommendFeedbackRequest,
    RecommendFeedbackResponse,
    RecommendedContent,
    RecommendRequest,
    RecommendResponse,
)
from core.db import fetch_latest_context


router = APIRouter(prefix="/recommend", tags=["Recommendations"])


def get_database_url() -> str:
    """Get database URL from environment."""
    return os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/myapp"
    )


def fetch_user_preferences(user_id: str) -> dict | None:
    """Fetch user preferences and interaction history from database."""
    conn = psycopg2.connect(get_database_url())
    cursor = conn.cursor()

    try:
        # 1. Fetch preferences
        cursor.execute(
            """
            SELECT 
                selected_movie_ids,
                selected_song_ids,
                birth_year,
                experiment_group,
                nostalgic_period_start,
                nostalgic_period_end
            FROM user_preferences
            WHERE user_id = %s
            LIMIT 1;
        """,
            (user_id,),
        )

        pref_row = cursor.fetchone()

        if not pref_row:
            return None

        prefs = {
            "selected_movie_ids": pref_row[0] or [],
            "selected_song_ids": pref_row[1] or [],
            "birth_year": pref_row[2],
            "experiment_group": pref_row[3] or "treatment",
            "nostalgic_period_start": pref_row[4],
            "nostalgic_period_end": pref_row[5],
        }

        # 2. Fetch timestamps for selected items (from content_feedback if available)
        # Note: Onboarding selections might not have timestamps in feedback table initially,
        # so we default to "now" or "old" if missing.
        # Ideally, we should track onboarding timestamp.

        # Fetch actual feedback history with timestamps
        cursor.execute(
            """
            SELECT content_type, content_id, created_at
            FROM content_feedback
            WHERE user_id = %s AND brings_back_memories = true;
        """,
            (user_id,),
        )

        feedback_rows = cursor.fetchall()

        prefs["feedback_history"] = [
            {"type": r[0], "id": r[1], "timestamp": r[2].isoformat()}
            for r in feedback_rows
        ]

        return prefs
    finally:
        cursor.close()
        conn.close()


def fetch_recent_feedback(user_id: str, limit: int = 50) -> list[dict]:
    """Fetch recent feedback for a user from the database."""
    conn = psycopg2.connect(get_database_url())
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT content_type, content_id, brings_back_memories, created_at
            FROM content_feedback
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s;
        """,
            (user_id, limit),
        )

        rows = cursor.fetchall()
        return [
            {
                "content_type": r[0],
                "content_id": r[1],
                "brings_back_memories": r[2],
                "created_at": r[3].isoformat() if r[3] else None,
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Error fetching recent feedback: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def calculate_user_positive_rate(recent_feedback: list[dict]) -> float:
    """Calculate the positive feedback rate for a user."""
    if not recent_feedback:
        return 0.5  # Default neutral rate

    positive_count = sum(1 for f in recent_feedback if f.get("brings_back_memories"))
    return positive_count / len(recent_feedback)


@router.post(
    "",
    response_model=RecommendResponse,
    summary="Get personalized recommendation",
    description="Get a nostalgic content recommendation using weighted vectors and contextual bandits.",
)
async def get_recommendation(
    request: Request,
    body: RecommendRequest,
) -> RecommendResponse:
    """Get a personalized nostalgic recommendation."""

    # Get recommenders and bandit from app state
    movie_recommender = request.app.state.recommenders.get("movie")
    song_recommender = request.app.state.recommenders.get("song")
    stress_detector = request.app.state.recommenders.get("stress")
    emotion_detector = request.app.state.recommenders.get("emotion")
    bandit: HierarchicalBandit = request.app.state.recommenders.get("bandit")

    # Fetch user preferences
    prefs = fetch_user_preferences(body.user_id)
    if not prefs:
        raise HTTPException(
            status_code=400,
            detail="User preferences not found. Please complete onboarding.",
        )

    # Calculate Nostalgic Center (Legacy support, but we use birth year now)
    birth_year = prefs.get("birth_year") or 2000

    # Get custom nostalgic period if set
    target_period = None
    if prefs.get("nostalgic_period_start") and prefs.get("nostalgic_period_end"):
        target_period = (prefs["nostalgic_period_start"], prefs["nostalgic_period_end"])
        print(f"[DEBUG] Using custom nostalgic period: {target_period}")

    # Prepare Liked Items with Timestamps for Weighting
    liked_movies = []
    liked_songs = []

    # Add onboarding selections (default timestamp = None -> older weight)
    for mid in prefs["selected_movie_ids"]:
        liked_movies.append({"movieId": mid, "timestamp": None})
    for sid in prefs["selected_song_ids"]:
        liked_songs.append({"spotify_id": sid, "timestamp": None})

    # Overlay actual feedback history (overrides default timestamp if present)
    # We prioritize the specific timestamps from feedback
    for item in prefs["feedback_history"]:
        if item["type"] == "movie":
            # Add or update
            found = False
            for m in liked_movies:
                if str(m["movieId"]) == str(item["id"]):
                    m["timestamp"] = item["timestamp"]
                    found = True
                    break
            if not found:
                liked_movies.append(
                    {"movieId": int(item["id"]), "timestamp": item["timestamp"]}
                )

        elif item["type"] == "song":
            found = False
            for s in liked_songs:
                if str(s["spotify_id"]) == str(item["id"]):
                    s["timestamp"] = item["timestamp"]
                    found = True
                    break
            if not found:
                liked_songs.append(
                    {"spotify_id": item["id"], "timestamp": item["timestamp"]}
                )

    # Fetch recent feedback (for Context & Filtering)
    recent_feedback = fetch_recent_feedback(body.user_id)

    # DEBUG: Print what we're passing to recommenders
    print(
        f"[DEBUG] User {body.user_id}: {len(liked_movies)} liked movies, {len(liked_songs)} liked songs"
    )
    print(f"[DEBUG] Liked movie IDs: {[m['movieId'] for m in liked_movies]}")
    print(f"[DEBUG] Liked song IDs: {[s['spotify_id'] for s in liked_songs]}")
    user_positive_rate = calculate_user_positive_rate(recent_feedback)

    # Analyze journal text for stress and emotion
    stress_score = 0.5
    emotion_result = {"emotion": "neutral", "confidence": 0.5, "probabilities": {}}

    # 1. Analyze Context (Stress & Emotion)
    if body.journal_text and body.journal_text.strip():
        if stress_detector:
            try:
                stress_score = stress_detector.predict(body.journal_text)
            except Exception as e:
                print(f"Stress detection error: {e}")

        if emotion_detector:
            try:
                emotion_result = emotion_detector.predict(body.journal_text)
            except Exception as e:
                print(f"Emotion detection error: {e}")

    else:
        # "New Pick" scenario: Fetch cached context
        db_context = fetch_latest_context(body.user_id)
        stress_score = db_context["stress_score"]
        current_emotion = db_context["emotion"]
        emotion_result = {
            "emotion": current_emotion,
            "confidence": 1.0,
            "probabilities": {current_emotion: 1.0},
        }

    # Build context features for bandit
    context = build_context_features(
        stress_score=stress_score,
        emotion=emotion_result["emotion"],
        user_positive_rate=user_positive_rate,
        birth_year=birth_year,
    )

    # Generate candidates
    candidates: list[dict] = []

    # Constants for nostalgia scoring
    # These are approximate max values - in production, query from DB
    MAX_MOVIE_RATINGS = 100000.0
    MAX_SONG_POPULARITY = 100.0
    MIN_NOSTALGIA_SCORE = 0.3  # Threshold for nostalgic content

    # Control Group: Random Recommendations
    if prefs.get("experiment_group") == "control":
        print(
            f"[DEBUG] User {body.user_id} is in CONTROL group. Generating random recommendations."
        )

        # Random Movies
        if movie_recommender:
            try:
                random_movies = movie_recommender.get_random_recommendations(n=25)
                for _, row in random_movies.iterrows():
                    candidates.append(
                        {
                            "type": "movie",
                            "id": row["movieId"],
                            "title": row["title"],
                            "genres": row["genres"],
                            "year": row["year"],
                            "rating_count": row.get("rating_count", 0),
                            "nostalgia_score": 0.0,
                            "similarity_score": 0.0,
                        }
                    )
            except Exception as e:
                print(f"Control group movie error: {e}")

        # Random Songs
        if song_recommender:
            try:
                random_songs = song_recommender.get_random_recommendations(n=25)
                for _, row in random_songs.iterrows():
                    candidates.append(
                        {
                            "type": "song",
                            "id": row["spotify_id"],
                            "name": row["name"],
                            "artists": row["artists"],
                            "genre": row["genre"],
                            "year": row["year"],
                            "popularity": 50,
                            "nostalgia_score": 0.0,
                            "similarity_score": 0.0,
                        }
                    )
            except Exception as e:
                print(f"Control group song error: {e}")

        # Skip nostalgia enforcement and bandit scoring for control group
        # Just filter recent feedback and shuffle
        if recent_feedback:
            recent_ids = {str(f["content_id"]) for f in recent_feedback}
            candidates = [c for c in candidates if str(c["id"]) not in recent_ids]

        import random

        if candidates:
            random.shuffle(candidates)
            selected = candidates[0]
            bandit_score = 0.5
        else:
            raise HTTPException(
                status_code=503,
                detail="No candidates available for control group.",
            )

    else:
        # Treatment Group: Nostalgic Recommendations (Existing Logic)

        # Movie candidates
        if movie_recommender and liked_movies:
            try:
                # Pass None for years to get broader range (we filter/tag manually later if needed)
                movie_df = movie_recommender.recommend(
                    liked_items=liked_movies,
                    n_recommendations=50,
                )
                print(f"[DEBUG] Generated {len(movie_df)} movie candidates.")
                for _, row in movie_df.iterrows():
                    movie_year = row.get("year")
                    rating_count = row.get("rating_count", 0) or 0

                    # Calculate nostalgia score
                    ns = (
                        nostalgia_score(
                            birth_year=birth_year or 2000,
                            release_year=int(movie_year) if movie_year else 2000,
                            rating_count=float(rating_count),
                            max_count=MAX_MOVIE_RATINGS,
                            target_period=target_period,
                        )
                        if movie_year
                        else 0.0
                    )

                    candidates.append(
                        {
                            "type": "movie",
                            "id": row["movieId"],
                            "title": row["title"],
                            "genres": row["genres"],
                            "year": movie_year,
                            "rating_count": rating_count,
                            "nostalgia_score": ns,
                            "similarity_score": row.get("score", 0.5),
                        }
                    )
            except Exception as e:
                print(f"Movie recommendation error: {e}")
                import traceback

                traceback.print_exc()

        # Song candidates
        if song_recommender and liked_songs:
            try:
                song_df = song_recommender.recommend(
                    liked_items=liked_songs,
                    n_recommendations=50,
                )
                print(f"[DEBUG] Generated {len(song_df)} song candidates.")
                for _, row in song_df.iterrows():
                    song_year = int(row["year"]) if pd.notna(row["year"]) else None
                    song_popularity = row.get("popularity", 50) or 50

                    # Calculate nostalgia score
                    ns = (
                        nostalgia_score(
                            birth_year=birth_year or 2000,
                            release_year=song_year or 2000,
                            rating_count=float(
                                song_popularity
                            ),  # Use popularity as proxy
                            max_count=MAX_SONG_POPULARITY,
                            use_linear=True,  # Spotify popularity is already 0-100 normalized
                            target_period=target_period,
                        )
                        if song_year
                        else 0.0
                    )

                    candidates.append(
                        {
                            "type": "song",
                            "id": row["spotify_id"],
                            "name": row["name"],
                            "artists": row["artists"],
                            "genre": row["genre"],
                            "year": song_year,
                            "popularity": song_popularity,
                            "nostalgia_score": ns,
                            "similarity_score": row.get("score", 0.5),
                        }
                    )
            except Exception as e:
                print(f"Song recommendation error: {e}")
                import traceback

                traceback.print_exc()
        else:
            print(
                f"[DEBUG] Skipping songs. Recommender: {song_recommender is not None}, Liked Songs: {len(liked_songs)}"
            )

        # Filter out candidates user has already reacted to recently
        if recent_feedback:
            recent_ids = {str(f["content_id"]) for f in recent_feedback}
            candidates = [c for c in candidates if str(c["id"]) not in recent_ids]

        # === NOSTALGIA ENFORCEMENT ===
        # Note: Recommenders already filter by 10-year minimum age at DB level.
        # This is a secondary filter by nostalgia score for users with specific birth years.
        nostalgic_candidates = [
            c for c in candidates if c.get("nostalgia_score", 0) >= MIN_NOSTALGIA_SCORE
        ]

        if nostalgic_candidates:
            # Log distribution
            scores = [c["nostalgia_score"] for c in nostalgic_candidates]
            print(
                f"[NOSTALGIA] Filtered {len(candidates)} -> {len(nostalgic_candidates)} nostalgic candidates (score >= {MIN_NOSTALGIA_SCORE})"
            )
            print(
                f"[NOSTALGIA] Score range: {min(scores):.2f} - {max(scores):.2f}, avg: {sum(scores) / len(scores):.2f}"
            )
            candidates = nostalgic_candidates
        else:
            # All candidates are already 10+ years old from recommenders.
            # If nostalgia_score filtering removed all, use all candidates (they're still old enough).
            print(
                f"[NOSTALGIA] Warning: No high nostalgia-score candidates. Using {len(candidates)} candidates (all 10+ years old)."
            )

        # Fallback
        if not candidates:
            raise HTTPException(
                status_code=503,
                detail="No candidates available. Ensure recommenders are loaded.",
            )

        # Shuffle candidates to prevent positional bias (e.g. favoring movies because they are first)
        import random

        random.shuffle(candidates)

        # Use bandit to select best candidate
        if bandit:
            try:
                # Get raw scores for debugging
                context_2d = bandit.global_model._ensure_context_shape(context)
                candidate_arms = [
                    bandit.global_model._get_arm_from_candidate(c) for c in candidates
                ]

                # Predict
                predictions = bandit.global_model.mab.predict_expectations(context_2d)

                # Handle list return type (mabwiser returns list for 2D input)
                if isinstance(predictions, list):
                    predictions = predictions[0]

                score_summary = []
                for arm in set(candidate_arms):
                    score_summary.append(f"{arm}: {predictions.get(arm, 0.0):.3f}")
                print(f"[DEBUG] Bandit Predictions: {', '.join(score_summary)}")

                selected_idx, bandit_score = bandit.select(
                    user_id=body.user_id,
                    context=context,
                    candidates=candidates,
                )

                # Within-arm selection: pick best similarity within the chosen arm
                selected_arm = bandit.global_model._get_arm_from_candidate(
                    candidates[selected_idx]
                )
                arm_candidates = [
                    (i, c)
                    for i, c in enumerate(candidates)
                    if bandit.global_model._get_arm_from_candidate(c) == selected_arm
                ]

                if len(arm_candidates) > 1:
                    # Stochastic Selection: Pick from top 5 highest similarity candidates
                    # This ensures variety instead of always picking the same #1 item
                    arm_candidates.sort(
                        key=lambda x: x[1].get("similarity_score", 0), reverse=True
                    )
                    top_n = arm_candidates[:5]

                    import random

                    best_idx, selected = random.choice(top_n)
                    print(
                        f"[DEBUG] Within-arm selection: picked random from top {len(top_n)} of {len(arm_candidates)} candidates in '{selected_arm}'"
                    )
                else:
                    selected = candidates[selected_idx]

                print(
                    f"[DEBUG] Selected: {selected.get('title') or selected.get('name')} | Arm: {selected_arm} | Nostalgia: {selected.get('nostalgia_score', 0):.2f}"
                )
            except Exception as e:
                print(f"Bandit selection error: {e}")
                selected = candidates[0]
                bandit_score = 0.5
        else:
            import random

            selected = random.choice(candidates)
            bandit_score = 0.5

    # Build response
    if selected["type"] == "movie":
        content = RecommendedContent(
            type="movie",
            id=str(selected["id"]),
            title=selected.get("title", "Unknown"),
            year=selected.get("year"),
            genres=selected.get("genres", "").split("|")
            if selected.get("genres")
            else None,
            artists=None,
            name=None,
            genre=None,
        )
    else:
        content = RecommendedContent(
            type="song",
            id=str(selected["id"]),
            name=selected.get("name", "Unknown"),
            artists=selected.get("artists", "").split(", ")
            if isinstance(selected.get("artists"), str)
            else selected.get("artists"),
            year=selected.get("year"),
            genre=selected.get("genre"),
            title=None,
            genres=None,
        )

    return RecommendResponse(
        content=content,
        stress_score=stress_score,
        emotion=EmotionResult(
            emotion=emotion_result["emotion"],
            confidence=emotion_result.get("confidence", 0.5),
            probabilities=emotion_result.get("probabilities", {}),
        ),
        bandit_score=bandit_score,
    )


@router.post(
    "/feedback",
    response_model=RecommendFeedbackResponse,
    summary="Submit recommendation feedback",
    description="Update the bandit model with user feedback on a recommendation.",
)
async def submit_feedback(
    request: Request,
    body: RecommendFeedbackRequest,
) -> RecommendFeedbackResponse:
    """Submit feedback for a recommendation to update the bandit."""

    bandit: HierarchicalBandit = request.app.state.recommenders.get("bandit")

    if not bandit:
        raise HTTPException(
            status_code=503,
            detail="Bandit model not loaded.",
        )

    # Need to reconstruct the arm for update
    # We need the genre and year to map to the correct arm
    # Ideally frontend sends this back, but for now we might need to fetch it or approximation
    # Since we can't easily fetch year without querying DB again, we'll try to use the body info
    # The body has content_year and content_genre!

    # Fetch user prefs to get birth year
    prefs = fetch_user_preferences(body.user_id)
    if prefs:
        birth_year = prefs["birth_year"] or 2000
    else:
        birth_year = 2000

    # Build candidate info for update
    candidate = {
        "type": body.content_type,
        "id": body.content_id,
        "year": body.content_year,
        "genre": body.content_genre,
        "genres": body.content_genre,
    }

    # Calculate reward
    reward = calculate_reward(
        interaction_type=body.interaction_type,
        brings_back_memories=body.brings_back_memories,
        duration_seconds=body.duration_seconds or 0,
        feedback_submitted=body.feedback_submitted,
    )

    if reward is None:
        return RecommendFeedbackResponse(
            success=True,  # Client call succeeded, we just didn't learn from it
            reward=0.0,
            message=f"Interaction '{body.interaction_type}' ignored (no reward signal).",
        )

    # Context (Prefer snapshot from request, fallback to approximate)
    recent_feedback = fetch_recent_feedback(body.user_id)
    user_positive_rate = calculate_user_positive_rate(recent_feedback)

    # Use the context from when the recommendation was made, if provided
    stress_context = body.context_stress if body.context_stress is not None else 0.5
    emotion_context = body.context_emotion if body.context_emotion else "neutral"

    context = build_context_features(
        stress_score=stress_context,
        emotion=emotion_context,
        user_positive_rate=user_positive_rate,
        birth_year=birth_year,
    )

    # Update bandit
    try:
        bandit.update(
            user_id=body.user_id,
            context=context,
            candidate=candidate,
            reward=reward,
        )
    except Exception as e:
        print(f"Bandit update error: {e}")

    return RecommendFeedbackResponse(
        success=True,
        reward=reward,
        message=f"Feedback recorded ({body.interaction_type}, r={reward}) and bandit updated.",
    )


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze text for stress and emotion",
    description="Analyze journal text to detect stress levels and emotions without generating recommendations.",
)
async def analyze_text(
    request: Request,
    body: AnalyzeRequest,
) -> AnalyzeResponse:
    """Analyze text for stress and emotion."""

    stress_detector = request.app.state.recommenders.get("stress")
    emotion_detector = request.app.state.recommenders.get("emotion")

    stress_score = 0.5
    emotion_result = {"emotion": "neutral", "confidence": 0.5, "probabilities": {}}

    if body.text and body.text.strip():
        if stress_detector:
            try:
                stress_score = stress_detector.predict(body.text)
            except Exception as e:
                print(f"Stress detection error: {e}")

        if emotion_detector:
            try:
                emotion_result = emotion_detector.predict(body.text)
            except Exception as e:
                print(f"Emotion detection error: {e}")

    return AnalyzeResponse(
        stress_score=stress_score,
        emotion=EmotionResult(
            emotion=emotion_result["emotion"],
            confidence=emotion_result.get("confidence", 0.5),
            probabilities=emotion_result.get("probabilities", {}),
        ),
    )
