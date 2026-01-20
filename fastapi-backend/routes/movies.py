"""
Movie recommendation API routes.

This module provides endpoints for movie recommendations using the LightFM model.
"""

from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_movie_recommender
from services.movie_recommender import MovieRecommender
from core.schemas import (
    ErrorResponse,
    MovieInfo,
    MovieRecommendation,
    MovieRecommendRequest,
    MovieRecommendResponse,
    MovieSearchRequest,
    MovieSearchResponse,
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.post(
    "/recommend",
    response_model=MovieRecommendResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Get movie recommendations",
    description="Generate movie recommendations based on a list of movies the user has liked.",
)
async def recommend_movies(
    request: MovieRecommendRequest,
    recommender: MovieRecommender = Depends(get_movie_recommender),
) -> MovieRecommendResponse:
    """
    Get movie recommendations based on liked movies.

    Uses LightFM's user folding technique to generate personalized
    recommendations for new users (cold-start support).
    """
    try:
        # Get liked movies info
        liked_movies: list[MovieInfo] = []
        for movie_id in request.liked_movie_ids:
            info = recommender.get_movie_info(movie_id)
            if "error" not in info:
                liked_movies.append(
                    MovieInfo(
                        movie_id=int(info.get("movieId", movie_id)),
                        title=str(info.get("title", "Unknown")),
                        genres=str(info.get("genres", "")),
                        decade=str(info.get("decade", ""))
                        if info.get("decade")
                        else None,
                    )
                )

        # Generate recommendations
        recommendations_df = recommender.recommend(
            liked_items=[
                {"movieId": mid, "timestamp": None} for mid in request.liked_movie_ids
            ],  # Fix: adapt to new signature if needed, or check signature
            n_recommendations=request.n_recommendations,
            exclude_liked=request.exclude_liked,
            min_years_old=10,
        )

        recommendations: list[MovieRecommendation] = []
        for _, row in recommendations_df.iterrows():
            recommendations.append(
                MovieRecommendation(
                    movie_id=int(row["movieId"]),
                    title=str(row["title"]),
                    genres=str(row["genres"]),
                    decade=str(row["decade"]) if row.get("decade") else None,
                    score=float(row["score"]),
                )
            )

        return MovieRecommendResponse(
            recommendations=recommendations,
            liked_movies=liked_movies,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating recommendations: {e}"
        ) from e


@router.get(
    "/{movie_id}",
    response_model=MovieInfo,
    responses={
        404: {"model": ErrorResponse, "description": "Movie not found"},
    },
    summary="Get movie information",
    description="Get information about a specific movie by its MovieLens ID.",
)
async def get_movie(
    movie_id: int,
    recommender: MovieRecommender = Depends(get_movie_recommender),
) -> MovieInfo:
    """Get information about a specific movie."""
    info = recommender.get_movie_info(movie_id)

    if "error" in info:
        raise HTTPException(status_code=404, detail=f"Movie {movie_id} not found")

    return MovieInfo(
        movie_id=int(info.get("movieId", movie_id)),
        title=str(info.get("title", "Unknown")),
        genres=str(info.get("genres", "")),
        decade=str(info.get("decade", "")) if info.get("decade") else None,
    )


@router.post(
    "/search",
    response_model=MovieSearchResponse,
    summary="Search for movies",
    description="Search for movies by title.",
)
async def search_movies(
    request: MovieSearchRequest,
    recommender: MovieRecommender = Depends(get_movie_recommender),
) -> MovieSearchResponse:
    """Search for movies by title."""
    # Enforce 10-year age filter for nostalgic onboarding
    results_df = recommender.search_movies(
        request.query, limit=request.limit, min_years_old=10
    )

    results: list[MovieInfo] = []
    for _, row in results_df.iterrows():
        results.append(
            MovieInfo(
                movie_id=int(row["movieId"]),
                title=str(row["title"]),
                genres=str(row["genres"]),
                decade=str(row.get("decade", "")) if row.get("decade") else None,
            )
        )

    return MovieSearchResponse(
        results=results,
        query=request.query,
    )
