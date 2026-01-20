"""FastAPI Recommendation Server

This server provides endpoints for movie and song recommendations.
Models are loaded on startup using FastAPI's lifespan events.

Run with: uvicorn main:app --reload
"""

import os
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ENV_FILE = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_FILE)

from routes.movies import router as movies_router  # noqa: E402
from routes.songs import router as songs_router  # noqa: E402
from routes.stress import router as analyze_router  # noqa: E402
from routes.recommend import router as recommend_router  # noqa: E402
from core.schemas import HealthCheckResponse  # noqa: E402
from services.movie_recommender import MovieRecommender  # noqa: E402
from services.song_recommender import SongRecommender  # noqa: E402
from services.stress_detector import StressDetector  # noqa: E402
from services.emotion_detector import EmotionDetector  # noqa: E402
from services.contextual_bandit import HierarchicalBandit  # noqa: E402


# =============================================================================
# Configuration
# =============================================================================

API_VERSION = "1.0.0"
API_TITLE = "Nostalgic Recommendation API"
API_DESCRIPTION = """
A recommendation API for movies and songs using machine learning models.

## Features

- 🎬 **Movie Recommendations**: Using LightFM collaborative filtering with cold-start support
- 🎵 **Song Recommendations**: Using content-based filtering with pgvector similarity search
- 🔍 **Search**: Search movies by title, songs by name or artist
- ✨ **Validation**: Full request/response validation with Pydantic

## Models

- **Movie Recommender**: LightFM model trained on MovieLens 32M dataset
- **Song Recommender**: Content-based filtering using audio features, stored in pgvector
"""

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


# =============================================================================
# Model State
# =============================================================================


class AppState:
    """Application state container for recommenders."""

    movie_recommender: MovieRecommender | None = None
    song_recommender: SongRecommender | None = None
    movie_model_loaded: bool = False
    song_model_loaded: bool = False


# =============================================================================
# Lifespan Events
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifespan.

    On startup: Load movie and song recommendation models.
    On shutdown: Clean up resources.
    """
    print("=" * 60)
    print(f"🚀 Starting {API_TITLE} v{API_VERSION}")
    print("=" * 60)

    # Initialize state
    app.state.recommenders = {
        "movie": None,
        "song": None,
        "stress": None,
        "emotion": None,
        "bandit": None,
    }
    app.state.model_status = {
        "movie_loaded": False,
        "song_loaded": False,
        "stress_loaded": False,
        "emotion_loaded": False,
        "bandit_loaded": False,
    }

    # Load movie recommender
    print("\n📽️  Loading Movie Recommender...")
    try:
        movie_recommender = MovieRecommender()
        app.state.recommenders["movie"] = movie_recommender  # type: ignore[assignment]
        app.state.model_status["movie_loaded"] = True  # type: ignore[assignment]
        print("✅ Movie Recommender loaded successfully!")
    except FileNotFoundError as e:
        print(f"⚠️  Movie model files not found: {e}")
        print("   Movie recommendations will be unavailable.")
    except Exception as e:
        print(f"❌ Error loading Movie Recommender: {e}")
        traceback.print_exc()

    # Load song recommender
    print("\n🎵 Loading Song Recommender...")
    try:
        song_recommender = SongRecommender()
        app.state.recommenders["song"] = song_recommender  # type: ignore[assignment]
        app.state.model_status["song_loaded"] = True  # type: ignore[assignment]
        print("✅ Song Recommender loaded successfully!")
    except FileNotFoundError as e:
        print(f"⚠️  Song model files not found: {e}")
        print("   Song recommendations will be unavailable.")
    except Exception as e:
        print(f"❌ Error loading Song Recommender: {e}")
        print("   This may be due to database connection issues.")
        traceback.print_exc()

    # Load stress detector
    print("\n🧠  Loading Stress Detector...")
    try:
        stress_detector = StressDetector()
        app.state.recommenders["stress"] = stress_detector  # type: ignore[assignment]
        app.state.model_status["stress_loaded"] = True  # type: ignore[assignment]
        print("✅ Stress Detector loaded successfully!")
    except FileNotFoundError as e:
        print(f"⚠️  Stress model files not found: {e}")
        print("   Stress detection will be unavailable.")
    except Exception as e:
        print(f"❌ Error loading Stress Detector: {e}")
        traceback.print_exc()

    # Load emotion detector
    print("\n💭 Loading Emotion Detector...")
    try:
        emotion_detector = EmotionDetector(use_mock=False)
        app.state.recommenders["emotion"] = emotion_detector  # type: ignore[assignment]
        app.state.model_status["emotion_loaded"] = True  # type: ignore[assignment]
        print("✅ Emotion Detector loaded successfully!")
    except Exception as e:
        print(f"⚠️  Error loading real Emotion Detector: {e}")
        print("   Falling back to MOCK Emotion Detector.")
        try:
            emotion_detector = EmotionDetector(use_mock=True)
            app.state.recommenders["emotion"] = emotion_detector  # type: ignore[assignment]
            app.state.model_status["emotion_loaded"] = True  # type: ignore[assignment]
            print("✅ Mock Emotion Detector loaded.")
        except Exception as e2:
            print(f"❌ Error loading Mock Emotion Detector: {e2}")
            traceback.print_exc()

    # Load contextual bandit
    print("\n🎰 Loading Contextual Bandit...")
    try:
        bandit = HierarchicalBandit()
        app.state.recommenders["bandit"] = bandit  # type: ignore[assignment]
        app.state.model_status["bandit_loaded"] = True  # type: ignore[assignment]
        print("✅ Contextual Bandit loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading Contextual Bandit: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("🌐 Server is ready to accept requests")
    print("=" * 60 + "\n")

    # Yield control to the application
    yield

    # Cleanup on shutdown
    print("\n🛑 Shutting down server...")

    # Close database connections
    if app.state.recommenders["movie"]:
        app.state.recommenders["movie"].close()
        print("   Closed movie recommender database connection.")

    if app.state.recommenders["song"]:
        app.state.recommenders["song"].close()
        print("   Closed song recommender database connection.")

    if app.state.recommenders["stress"]:
        app.state.recommenders["stress"].close()
        print("   Closed stress detector.")

    if app.state.recommenders["emotion"]:
        app.state.recommenders["emotion"].close()
        print("   Closed emotion detector.")

    if app.state.recommenders["bandit"]:
        app.state.recommenders["bandit"].close()
        print("   Closed contextual bandit.")

    # Clear references
    app.state.recommenders["movie"] = None
    app.state.recommenders["song"] = None
    app.state.recommenders["stress"] = None
    app.state.recommenders["emotion"] = None
    app.state.recommenders["bandit"] = None

    print("👋 Server shutdown complete.\n")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health Check Endpoint
# =============================================================================


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Health check",
    description="Check the API status and model availability.",
)
async def health_check() -> HealthCheckResponse:
    """Return the API health status and model loading status."""
    return HealthCheckResponse(
        status="healthy",
        movie_model_loaded=app.state.model_status.get("movie_loaded", False),
        song_model_loaded=app.state.model_status.get("song_loaded", False),
        stress_model_loaded=app.state.model_status.get("stress_loaded", False),
        emotion_model_loaded=app.state.model_status.get("emotion_loaded", False),
        bandit_loaded=app.state.model_status.get("bandit_loaded", False),
        version=API_VERSION,
    )


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint with welcome message."""
    return {
        "message": f"Welcome to {API_TITLE}",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# =============================================================================
# Register Routers
# =============================================================================

app.include_router(movies_router)
app.include_router(songs_router)
app.include_router(analyze_router)
app.include_router(recommend_router)


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import signal
    import sys
    import uvicorn

    def shutdown_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, initiating graceful shutdown...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    print(f"\n🔧 Starting server on http://{host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
    )
