"""
Song recommendation API routes.

This module provides endpoints for song recommendations using pgvector.
"""

from typing import Any, Union

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_song_recommender
from services.song_recommender import SongRecommender
from core.schemas import (
    ErrorResponse,
    SongDetails,
    SongInfo,
    SongRecommendation,
    SongRecommendByIdRequest,
    SongRecommendRequest,
    SongRecommendResponse,
    SongSearchRequest,
    SongSearchResponse,
)


def _get_int(d: Union[dict[str, Any], pd.Series], key: str) -> int | None:
    """Safely get an int value from a dict or Series."""
    val = d.get(key)
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _get_float(d: Union[dict[str, Any], pd.Series], key: str) -> float | None:
    """Safely get a float value from a dict or Series."""
    val = d.get(key)
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


router = APIRouter(prefix="/songs", tags=["Songs"])


@router.post(
    "/recommend",
    response_model=SongRecommendResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Get song recommendations",
    description="Generate song recommendations based on a list of songs the user likes.",
)
async def recommend_songs(
    request: SongRecommendRequest,
    recommender: SongRecommender = Depends(get_song_recommender),
) -> SongRecommendResponse:
    """
    Get song recommendations based on liked songs.

    Uses content-based filtering with pgvector similarity search.
    Averages the embeddings of liked songs and finds similar songs.
    """
    try:
        # Get info for query songs
        query_songs: list[SongInfo] = []
        for song_id in request.liked_song_ids:
            info = recommender.get_song_info(song_id)
            if info:
                query_songs.append(
                    SongInfo(
                        spotify_id=str(info.get("id", song_id)),
                        name=str(info.get("name", "Unknown")),
                        artists=str(info.get("artists", "Unknown")),
                        genre=str(info.get("genre")) if info.get("genre") else None,
                        year=_get_int(info, "year"),
                    )
                )

        # Generate recommendations - convert song IDs to the expected format
        liked_items = [
            {"spotify_id": sid, "timestamp": None} for sid in request.liked_song_ids
        ]
        recommendations_df = recommender.recommend(
            liked_items=liked_items,
            n_recommendations=request.n_recommendations,
            exclude_liked=request.exclude_liked,
            min_years_old=10,
        )

        if recommendations_df.empty:
            return SongRecommendResponse(
                recommendations=[],
                query_songs=query_songs,
            )

        recommendations: list[SongRecommendation] = []
        for _, row in recommendations_df.iterrows():
            recommendations.append(
                SongRecommendation(
                    spotify_id=str(row["spotify_id"]),
                    name=str(row["name"]),
                    artists=str(row["artists"]),
                    genre=str(row.get("genre")) if row.get("genre") else None,
                    year=_get_int(row, "year"),
                    similarity=_get_float(row, "similarity") or 0.0,
                )
            )

        return SongRecommendResponse(
            recommendations=recommendations,
            query_songs=query_songs,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating recommendations: {e}"
        ) from e


@router.post(
    "/recommend/by-id",
    response_model=SongRecommendResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Song not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Get song recommendations by single song ID",
    description="Generate song recommendations based on a single song.",
)
async def recommend_songs_by_id(
    request: SongRecommendByIdRequest,
    recommender: SongRecommender = Depends(get_song_recommender),
) -> SongRecommendResponse:
    """
    Get song recommendations based on a single song.

    Uses the pre-computed embedding from pgvector for fastest query.
    """
    try:
        # Get info for query song
        info = recommender.get_song_info(request.spotify_id)
        if not info:
            raise HTTPException(
                status_code=404,
                detail=f"Song {request.spotify_id} not found in database",
            )

        query_song = SongInfo(
            spotify_id=str(info.get("id", request.spotify_id)),
            name=str(info.get("name", "Unknown")),
            artists=str(info.get("artists", "Unknown")),
            genre=str(info.get("genre")) if info.get("genre") else None,
            year=_get_int(info, "year"),
        )

        # Generate recommendations
        recommendations_df = recommender.recommend_by_id(
            spotify_id=request.spotify_id,
            n_recommendations=request.n_recommendations,
        )

        recommendations: list[SongRecommendation] = []
        for _, row in recommendations_df.iterrows():
            recommendations.append(
                SongRecommendation(
                    spotify_id=str(row["spotify_id"]),
                    name=str(row["name"]),
                    artists=str(row["artists"]),
                    genre=str(row.get("genre")) if row.get("genre") else None,
                    year=_get_int(row, "year"),
                    similarity=_get_float(row, "similarity") or 0.0,
                )
            )

        return SongRecommendResponse(
            recommendations=recommendations,
            query_songs=[query_song],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating recommendations: {e}"
        ) from e


@router.get(
    "/{spotify_id}",
    response_model=SongDetails,
    responses={
        404: {"model": ErrorResponse, "description": "Song not found"},
    },
    summary="Get song information",
    description="Get detailed information about a specific song by its Spotify ID.",
)
async def get_song(
    spotify_id: str,
    recommender: SongRecommender = Depends(get_song_recommender),
) -> SongDetails:
    """Get detailed information about a specific song."""
    info = recommender.get_song_info(spotify_id)

    if not info:
        raise HTTPException(status_code=404, detail=f"Song {spotify_id} not found")

    return SongDetails(
        spotify_id=str(info.get("id", spotify_id)),
        name=str(info.get("name", "Unknown")),
        artists=str(info.get("artists", "Unknown")),
        genre=str(info.get("genre")) if info.get("genre") else None,
        year=_get_int(info, "year"),
        danceability=_get_float(info, "danceability"),
        energy=_get_float(info, "energy"),
        key=_get_int(info, "key"),
        loudness=_get_float(info, "loudness"),
        mode=_get_int(info, "mode"),
        speechiness=_get_float(info, "speechiness"),
        acousticness=_get_float(info, "acousticness"),
        instrumentalness=_get_float(info, "instrumentalness"),
        liveness=_get_float(info, "liveness"),
        valence=_get_float(info, "valence"),
        tempo=_get_float(info, "tempo"),
        niche_genres=str(info.get("niche_genres"))
        if info.get("niche_genres")
        else None,
    )


@router.post(
    "/search",
    response_model=SongSearchResponse,
    summary="Search for songs",
    description="Search for songs by name or artist.",
)
async def search_songs(
    request: SongSearchRequest,
    recommender: SongRecommender = Depends(get_song_recommender),
) -> SongSearchResponse:
    """Search for songs by name or artist."""
    try:
        # Enforce 10-year age filter for nostalgic onboarding
        results_df = recommender.search_songs(
            request.query, limit=request.limit, min_years_old=10
        )

        results: list[SongInfo] = []
        for _, row in results_df.iterrows():
            results.append(
                SongInfo(
                    spotify_id=str(row["spotify_id"]),
                    name=str(row["name"]),
                    artists=str(row["artists"]),
                    genre=str(row.get("genre")) if row.get("genre") else None,
                    year=_get_int(row, "year"),
                )
            )

        return SongSearchResponse(
            results=results,
            query=request.query,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error searching songs: {e}"
        ) from e
