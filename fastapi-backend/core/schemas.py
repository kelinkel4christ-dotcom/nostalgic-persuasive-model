"""
Pydantic schemas for request and response validation.

This module defines all the data models used for API request/response
validation and serialization.
"""

from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


# =============================================================================
# Movie Schemas
# =============================================================================


class MovieBase(BaseModel):
    """Base movie schema with common fields."""

    movie_id: int = Field(..., description="MovieLens movieId")
    title: str = Field(..., description="Movie title")
    genres: str = Field(
        ..., description="Pipe-separated genres (e.g., 'Action|Comedy')"
    )


class MovieInfo(MovieBase):
    """Full movie information response."""

    decade: Optional[str] = Field(
        None, description="Decade the movie was released (e.g., '1990s')"
    )


class MovieRecommendation(MovieInfo):
    """Movie recommendation with score."""

    score: float = Field(..., description="Recommendation score (higher is better)")


class MovieRecommendRequest(BaseModel):
    """Request model for movie recommendations."""

    liked_movie_ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of MovieLens movieIds the user has liked",
    )
    n_recommendations: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of recommendations to return",
    )
    exclude_liked: bool = Field(
        default=True,
        description="Whether to exclude liked movies from recommendations",
    )


class MovieRecommendResponse(BaseModel):
    """Response model for movie recommendations."""

    recommendations: list[MovieRecommendation]
    liked_movies: list[MovieInfo]


class MovieSearchRequest(BaseModel):
    """Request model for movie search."""

    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum number of results"
    )


class MovieSearchResponse(BaseModel):
    """Response model for movie search."""

    results: list[MovieInfo]
    query: str


# =============================================================================
# Song Schemas
# =============================================================================


class SongBase(BaseModel):
    """Base song schema with common fields."""

    spotify_id: str = Field(..., description="Spotify track ID")
    name: str = Field(..., description="Song name")
    artists: str = Field(..., description="Artist name(s)")


class SongInfo(SongBase):
    """Full song information response."""

    genre: Optional[str] = Field(None, description="Genre of the song")
    year: Optional[int] = Field(None, description="Release year")


class SongDetails(SongInfo):
    """Extended song information with audio features."""

    danceability: Optional[float] = Field(
        None, ge=0, le=1, description="Danceability score"
    )
    energy: Optional[float] = Field(None, ge=0, le=1, description="Energy score")
    key: Optional[int] = Field(None, ge=0, le=11, description="Musical key (0-11)")
    loudness: Optional[float] = Field(None, description="Loudness in dB")
    mode: Optional[int] = Field(None, ge=0, le=1, description="Mode (0=minor, 1=major)")
    speechiness: Optional[float] = Field(
        None, ge=0, le=1, description="Speechiness score"
    )
    acousticness: Optional[float] = Field(
        None, ge=0, le=1, description="Acousticness score"
    )
    instrumentalness: Optional[float] = Field(
        None, ge=0, le=1, description="Instrumentalness score"
    )
    liveness: Optional[float] = Field(None, ge=0, le=1, description="Liveness score")
    valence: Optional[float] = Field(
        None, ge=0, le=1, description="Valence (happiness) score"
    )
    tempo: Optional[float] = Field(None, ge=0, description="Tempo in BPM")
    niche_genres: Optional[str] = Field(None, description="Niche genre tags")


class SongRecommendation(SongInfo):
    """Song recommendation with similarity score."""

    similarity: float = Field(
        ..., ge=0, le=1, description="Cosine similarity score (0-1)"
    )


class SongRecommendRequest(BaseModel):
    """Request model for song recommendations based on liked songs."""

    liked_song_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of Spotify track IDs the user likes",
    )
    n_recommendations: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of recommendations to return",
    )
    exclude_liked: bool = Field(
        default=True,
        description="Whether to exclude liked songs from recommendations",
    )


class SongRecommendByIdRequest(BaseModel):
    """Request model for song recommendations based on a single song."""

    spotify_id: str = Field(..., description="Spotify track ID")
    n_recommendations: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of recommendations to return",
    )


class SongRecommendResponse(BaseModel):
    """Response model for song recommendations."""

    recommendations: list[SongRecommendation]
    query_songs: list[SongInfo]


class SongSearchRequest(BaseModel):
    """Request model for song search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Search query for song name or artist",
    )
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum number of results"
    )


class SongSearchResponse(BaseModel):
    """Response model for song search."""

    results: list[SongInfo]
    query: str


# =============================================================================
# Text Analysis Schemas (Stress + Emotion Detection)
# =============================================================================


class TextAnalysisRequest(BaseModel):
    """Request model for text analysis (stress and emotion detection)."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to analyze for stress and emotion",
    )


class EmotionResult(BaseModel):
    """Emotion detection result."""

    emotion: str = Field(
        ...,
        description="Predicted emotion (anger, fear, joy, love, neutral, sadness, surprise)",
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence score for the prediction",
    )
    probabilities: dict[str, float] = Field(
        ...,
        description="Probability distribution across all emotions",
    )


class TextAnalysisResponse(BaseModel):
    """Response model for text analysis."""

    text: str = Field(..., description="The analyzed text")
    stress_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Stress level (0=no stress, 1=high stress)",
    )
    emotion: EmotionResult = Field(..., description="Detected emotion")


class AnalyzeRequest(BaseModel):
    """Request model for text analysis."""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")


class AnalyzeResponse(BaseModel):
    """Response model for text analysis."""

    stress_score: float = Field(..., ge=0, description="Stress level")
    emotion: EmotionResult = Field(..., description="Detected emotion")


# Legacy schemas for backwards compatibility
class StressDetectionRequest(BaseModel):
    """Request model for stress detection (legacy)."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to analyze for stress",
    )


class StressDetectionResponse(BaseModel):
    """Response model for stress detection (legacy)."""

    stress_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Stress level (0=no stress, 1=high stress)",
    )
    text: str = Field(..., description="The analyzed text")


# =============================================================================
# Health Check Schema
# =============================================================================


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="API status")
    movie_model_loaded: bool = Field(..., description="Whether movie model is loaded")
    song_model_loaded: bool = Field(..., description="Whether song model is loaded")
    stress_model_loaded: bool = Field(..., description="Whether stress model is loaded")
    emotion_model_loaded: bool = Field(
        ..., description="Whether emotion model is loaded"
    )
    bandit_loaded: bool = Field(..., description="Whether bandit model is loaded")
    version: str = Field(..., description="API version")


# =============================================================================
# Unified Recommendation Schemas
# =============================================================================


class RecommendRequest(BaseModel):
    """Request model for unified recommendation endpoint."""

    user_id: str = Field(..., description="User ID")
    journal_text: str = Field(
        default="",
        max_length=5000,
        description="Journal text to analyze for stress and emotion",
    )


class RecommendedContent(BaseModel):
    """Recommended content (either song or movie)."""

    type: str = Field(..., description="Content type: 'song' or 'movie'")
    id: str = Field(
        ..., description="Content ID (spotify_id for songs, movieId for movies)"
    )

    # Movie fields
    title: Optional[str] = Field(None, description="Movie title")
    genres: Optional[list[str]] = Field(None, description="Movie genres")

    # Song fields
    name: Optional[str] = Field(None, description="Song name")
    artists: Optional[list[str]] = Field(None, description="Song artists")
    genre: Optional[str] = Field(None, description="Song genre")

    # Common fields
    year: Optional[int] = Field(None, description="Release year")


class RecommendResponse(BaseModel):
    """Response model for unified recommendation endpoint."""

    content: RecommendedContent = Field(..., description="Recommended content")
    stress_score: float = Field(..., ge=0, le=1, description="Detected stress level")
    emotion: EmotionResult = Field(..., description="Detected emotion")
    bandit_score: float = Field(..., ge=0, description="Bandit confidence score")


class RecommendFeedbackRequest(BaseModel):
    """Request model for recommendation feedback."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    user_id: str = Field(..., description="User ID")
    content_type: str = Field(..., description="Content type: 'song' or 'movie'")
    content_id: str = Field(..., description="Content ID")

    # Interaction fields
    interaction_type: str = Field(
        default="feedback",
        description="Type of interaction (feedback, view, click, skip, next, replay)",
    )
    duration_seconds: Optional[int] = Field(
        None, description="Duration of interaction in seconds"
    )
    feedback_submitted: bool = Field(
        default=False,
        description="Whether explicit feedback has already been submitted for this session",
    )

    # Primary feedback signal (optional now, as implicit interactions might not have it)
    brings_back_memories: Optional[bool] = Field(
        None, description="Primary feedback signal"
    )

    # Content metadata for bandit update
    content_year: Optional[int] = Field(None, description="Content year")
    content_genre: Optional[str] = Field(None, description="Content genre")

    # Context snapshot (state at time of recommendation)
    context_stress: Optional[float] = Field(
        None, description="Stress score when recommendation was made"
    )
    context_emotion: Optional[str] = Field(
        None, description="Emotion when recommendation was made"
    )


class RecommendFeedbackResponse(BaseModel):
    """Response model for recommendation feedback."""

    success: bool = Field(..., description="Whether feedback was recorded")
    reward: float = Field(..., ge=0, le=1, description="Calculated reward value")
    message: str = Field(..., description="Status message")


# =============================================================================
# Error Schemas
# =============================================================================


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error message")
    error_type: str = Field(default="error", description="Type of error")
