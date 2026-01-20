---
title: Nostalgic Recommendation API
emoji: 🎬
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
app_port: 7860
---

# Nostalgic Recommendation API

FastAPI backend for movie and song recommendations using machine learning.

## Features

- Movie Recommendations using LightFM collaborative filtering
- Song Recommendations using content-based filtering with vector similarity
- Stress and Emotion Detection
- Contextual Bandit for personalized recommendations

## Endpoints

- `GET /health` - Health check and model status
- `GET /docs` - Interactive API documentation
- `POST /movies/recommend` - Get movie recommendations
- `POST /songs/recommend` - Get song recommendations
