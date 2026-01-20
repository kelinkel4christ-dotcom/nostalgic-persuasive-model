"""
Dependency injection for FastAPI routes.

This module provides dependencies for accessing the loaded recommenders
via FastAPI's dependency injection system.
"""

from typing import TypedDict

from fastapi import Request

from services.movie_recommender import MovieRecommender
from services.song_recommender import SongRecommender


class Recommenders(TypedDict):
    """Type definition for the recommenders state."""

    movie: MovieRecommender | None
    song: SongRecommender | None


def get_movie_recommender(request: Request) -> MovieRecommender:
    """
    Dependency to get the movie recommender from app state.

    Args:
        request: FastAPI request object

    Returns:
        MovieRecommender instance

    Raises:
        RuntimeError: If movie recommender is not loaded
    """
    recommenders: Recommenders = request.app.state.recommenders
    if recommenders["movie"] is None:
        raise RuntimeError("Movie recommender not loaded. Check server startup logs.")
    return recommenders["movie"]


def get_song_recommender(request: Request) -> SongRecommender:
    """
    Dependency to get the song recommender from app state.

    Args:
        request: FastAPI request object

    Returns:
        SongRecommender instance

    Raises:
        RuntimeError: If song recommender is not loaded
    """
    recommenders: Recommenders = request.app.state.recommenders
    if recommenders["song"] is None:
        raise RuntimeError("Song recommender not loaded. Check server startup logs.")
    return recommenders["song"]
