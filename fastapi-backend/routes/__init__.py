"""Routes package - API endpoint modules."""

from routes.movies import router as movies_router
from routes.songs import router as songs_router
from routes.recommend import router as recommend_router
from routes.stress import router as stress_router

__all__ = ["movies_router", "songs_router", "recommend_router", "stress_router"]
